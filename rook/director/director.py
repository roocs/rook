from collections import OrderedDict
from pywps.app.exceptions import ProcessError

from daops.utils import is_characterised, fixer
from roocs_utils.project_utils import get_project_name

from .inventory import Inventory
from .alignment import SubsetAlignmentChecker


class Director:

    def __init__(self, coll, inputs):
        self.coll = coll
        self.inputs = inputs

        # self.project = get_project_name(coll[0])
        self.project = "c3s-cmip6"

        try:
            self.inv = Inventory(self.project)
        except KeyError:
            self.process_error()

        self.use_original_files = False
        self.original_file_urls = None
        self._resolve()

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
        # Raise exception if any of the data is not in the inventory
        if not self.inv.contains(self.coll):
            self.process_error()

        # If original files are requested then go straight there
        if self.inputs.get('original_files'):
            self.use_original_files = True
            self.original_file_urls = self.inv.get_file_urls(self.coll)
            return

        # Raise exception if "pre_checked" selected but data has not been characterised by dachar
        if self.inputs.get('pre_checked') and not is_characterised(self.coll, require_all=True):
            raise ProcessError('Data has not been pre-checked')

        # Check if fixes are required. If so, then return (and subset will be generated).
        if self.inputs.get('apply_fixes') and self.requires_fixes():
            return 
        
        # Finally, check if the subset requirements can align with whole datasets
        if self.request_aligns_with_files():
            # This call sets values for self.original_file_urls AND self.use_original_files
            pass

        # If we got here: then WPS will be used, because `self.use_original_files == False`

    def process_error(self):
        raise ProcessError('Some or all of the requested collection are not in the list'
                           ' of available data.')
        
    def requires_fixes(self):
        for ds_id in self.inv.get_matches(self.coll):
            fix = fixer.Fixer(ds_id)

            if fix.pre_processor or fix.post_processors:
                return True

        return False

    def request_aligns_with_files(self):
        """
        Checks if files in the collection are aligned with the subset request.
        E.g.:
            coll = [dset1, dset2]
            inputs = {'time': '1999-01-01/2000-12-31'}

        If dset1 and dset2 have files that exactly start/end on those times, then:
            - return True (and the original files are provided).

        If, however, there are other subset options OR one of the datasets does not
        align, then:
            - return False (and the WPS is used to generate the output files).

        return: boolean
        """
        files = self.inv.get_file_urls(self.coll)
        required_files = OrderedDict()

        for ds_id, fpaths in files.items():
            sac = SubsetAlignmentChecker(fpaths, self.inputs)

            if not sac.is_aligned:
                self.use_original_files = False
                self.original_file_urls = None
                return False

            required_files[ds_id] = sac.aligned_files[:]

        # If we got here, then we have full alignment so set the properties and return True
        self.use_original_files = True
        self.original_file_urls = required_files

        return True
