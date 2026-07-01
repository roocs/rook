from pywps.app.exceptions import ProcessError
from clisops.utils.file_utils import FileMapper

from ..utils.input_utils import clean_inputs
from .compat import ResultSet
from .planning import plan_request


def wrap_director(collection, inputs, runner):
    # Ask director whether request should be rejected, use original files or apply WPS process
    try:
        director = Director(collection, inputs)
        director.process(runner)
        return director
    except Exception as e:
        raise ProcessError(f"{e}")


class Director:
    def __init__(self, collection, inputs):
        self.collection = collection
        self.inputs = inputs

        self.plan = plan_request(collection, inputs)
        self.output_uris = None

    @property
    def project(self):
        """Return the project resolved for the request."""
        return self.plan.project

    @property
    def use_original_files(self):
        """Return whether processing should be skipped."""
        return self.plan.returns_original_files

    @property
    def original_file_urls(self):
        """Return original files selected by the request plan."""
        return self.plan.original_file_urls

    @property
    def search_result(self):
        """Return the catalog search result, when catalog lookup was used."""
        return self.plan.search_result

    def process(self, runner):
        if self.use_original_files:
            file_uris = self._collect_original_file_uris()
        else:
            file_uris = self._run_operation(runner)

        self.output_uris = file_uris

    def _collect_original_file_uris(self):
        result = ResultSet()

        for ds_id, file_urls in self.original_file_urls.items():
            result.add(ds_id, file_urls)

        return result.file_uris

    def _run_operation(self, runner):
        operation_inputs = self._operation_inputs()

        try:
            return runner(operation_inputs)
        except Exception as e:
            raise ProcessError(f"{e}")

    def _operation_inputs(self):
        operation_inputs = dict(self.inputs)
        clean_inputs(operation_inputs)

        if self.search_result:
            operation_inputs["collection"] = []
            for ds_id, file_uris in self.search_result.files().items():
                file_mapper = FileMapper(file_uris)
                file_mapper.dataset_id = ds_id
                operation_inputs["collection"].append(file_mapper)

        return operation_inputs
