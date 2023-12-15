from collections import OrderedDict

from daops.utils import fixer, is_characterised
from daops.utils.normalise import ResultSet
from pywps.app.exceptions import ProcessError
from roocs_utils.project_utils import get_project_name
from roocs_utils.utils.file_utils import FileMapper

from rook import CONFIG
from roocs_utils.exceptions import InvalidCollection
from rook.catalog import get_catalog

from ..utils.input_utils import clean_inputs
from .alignment import SubsetAlignmentChecker


def wrap_director(collection, inputs, runner):
    # Ask director whether request should be rejected, use original files or apply WPS process
    try:
        director = Director(collection, inputs)
        director.process(runner)
        return director
    except Exception as e:
        raise ProcessError(f"{e}")


class Director:
    def __init__(self, coll, inputs):
        self.coll = coll
        self.inputs = inputs

        self.project = get_project_name(coll[0])
        # self.project = "c3s-cmip6"

        self.use_original_files = False
        self.original_file_urls = None
        self.output_uris = None
        self.search_result = None

        if CONFIG[f"project:{self.project}"].get("use_catalog"):
            try:
                self.catalog = get_catalog(self.project)
            except Exception:
                raise InvalidCollection()

            self._resolve()
        # if enabled for the project then check if a fix will be applied
        self._check_apply_fixes()

    def use_fixes(self):
        # TODO: don't use fixes
        return False
        # return CONFIG[f"project:{self.project}"].get("use_fixes", False)

    def _check_apply_fixes(self):
        if (
            self.use_fixes()
            and self.inputs.get("apply_fixes")
            and not self.use_original_files
            and self.requires_fixes()
        ):
            self.inputs["apply_fixes"] = True
        else:
            self.inputs["apply_fixes"] = False

    def _resolve(self):
        """
        Resolve how the WPS will handle this request. Steps through the following:
        - Are all datasets in the inventory?
            If NO: raise Exception
        - Does the user want to access original files only?
            If YES: return (and use original files)
        - Does the user require data to be pre-checked AND has the collection been pre-checked?
            If NO: raise Exception
        - Does the user want to apply fixes AND fixes are required for this collection?
            If YES: return (and use WPS)
        - Does the requested temporal subset align with files in all datasets in this collection?
            If YES: return (and use original files)
            If NO: return (and use WPS)

        Raises:
            ProcessError: [description]
            ProcessError: [description]
        """
        # search
        self.search_result = self.catalog.search(
            collection=self.coll,
            time=self.inputs.get("time"),
            time_components=self.inputs.get("time_components"),
        )
        # Raise exception if any of the dataset ids is not in the inventory
        if len(self.search_result) != len(self.coll):
            raise InvalidCollection()

        # If original files are requested then go straight there
        if (
            self.inputs.get("original_files")
            or self.project == "c3s-ipcc-atlas"
            or self.project == "c3s-cica-atlas"
        ):
            self.original_file_urls = self.search_result.download_urls()
            self.use_original_files = True
            return

        # Raise exception if "pre_checked" selected but data has not been characterised by dachar
        if self.inputs.get("pre_checked") and not is_characterised(
            self.coll, require_all=True
        ):
            raise ProcessError("Data has not been pre-checked")

        # Check if fixes are required. If so, then return (and subset will be generated).
        if self.inputs.get("apply_fixes") and self.requires_fixes():
            return

        # TODO: quick fix for average, regrid and concat. Don't use original files for these operators.
        if "dims" in self.inputs or "freq" in self.inputs or "grid" in self.inputs:
            return

        # Finally, check if the subset requirements can align with whole datasets
        if self.request_aligns_with_files():
            # This call sets values for self.original_file_urls AND self.use_original_files
            pass

        # If we got here: then WPS will be used, because `self.use_original_files == False`

    def requires_fixes(self):
        # TODO: don't use fixes
        return False
        # if not self.use_fixes():
        #     return False

        # if self.search_result:
        #     ds_ids = self.search_result.files()
        # else:
        #     ds_ids = self.coll
        # for ds_id in ds_ids:
        #     fix = fixer.Fixer(ds_id)

        #     if fix.pre_processor or fix.post_processors:
        #         return True

        # return False

    def request_aligns_with_files(self):
        """
        Checks if files in the collection are aligned with the subset request.
        E.g.:
            coll = [dset1, dset2]
            inputs = {'time': '1999-01-01/2000-12-31'}

        If input datasets have files that exactly start/end on those times, then:
            - return True (and the original files are provided).

        If, however, there are other subset options OR one of the datasets does not
        align, then:
            - return False (and the WPS is used to generate the output files).

        return: boolean
        """
        required_files = OrderedDict()

        for ds_id, urls in self.search_result.download_urls().items():
            sac = SubsetAlignmentChecker(urls, self.inputs)

            if not sac.is_aligned:
                self.use_original_files = False
                self.original_file_urls = None
                return False

            required_files[ds_id] = sac.aligned_files[:]

        # If we got here, then we have full alignment so set the properties and return True
        self.use_original_files = True
        self.original_file_urls = required_files

        return True

    def process(self, runner):
        # Either packages up original files (URLs) or
        # runs the process to generate the outputs
        # If original files should be returned, then add the files
        if self.use_original_files:
            result = ResultSet()

            for ds_id, file_urls in self.original_file_urls.items():
                result.add(ds_id, file_urls)

            file_uris = result.file_uris

        # else: generate the new subset of files
        else:
            clean_inputs(self.inputs)
            # use search result if available
            if self.search_result:
                self.inputs["collection"] = []
                for ds_id, file_uris in self.search_result.files().items():
                    self.inputs["collection"].append(FileMapper(file_uris))
            try:
                file_uris = runner(self.inputs)
            except Exception as e:
                raise ProcessError(f"{e}")

        # print("orig files", self.use_original_files)
        # print("uris", file_uris)

        self.output_uris = file_uris
