from daops.utils.core import is_characterised
from rook.files.search_inventory import Inventory, BuildURL
from roocs_utils.project_utils import get_project_name


class GetFiles:
    def __init__(self, operation, collection, kwargs):
        self.operation = operation
        self.collection = collection
        self.kwargs = kwargs
        # probably needs to take operation e.g. subset and kwargs related to this

    @staticmethod
    def quality_controlled(dset, project):
        inv = Inventory(project)
        return inv.dataset_exists(dset)

    # def is_characterised(self, dset):
    #     # check it is characterised using characterised class in daops (move that to here?)
    #     pass

    def find_fixes(self):
        # find fixes - to see if there are any! (use Fixer class)
        pass

    def get_files(self):
        # goes through decision logic and then calls correct function - either through daops or URL constructor
        # will be called by rook wps process

        # what happens with orchestrate - always WPS generated files

        # maybe this needs to be a separate class?
        results = []
        
        for dset in collection:
            project = get_project_name(dset)
            
            if not quality_controlled(self, dset, project):
                raise PermissionError("You do not have permission to access this dataset.")

            if kwargs.get('original_files') is True:
                urls = BuildURL(project).construct_urls(dset)
                results.append(urls)

        if kwargs.get('is_characterised') is True:
            resp = is_characterised(self.collection, require_all=True)
            if not resp:
                raise Exception("Some datasets have not been characterised.")
            # would be good to know which datasets

        pass
