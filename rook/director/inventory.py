import os
import yaml
from collections import OrderedDict

from roocs_utils import CONFIG

from .inv_cache import inventory_cache


DOWNLOAD_DIR_TEMPLATE = "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_{project}/"


class Inventory:

    def __init__(self, project):
        self.project = project
        self._load()
        
    def _load(self):
        inv_path = inventory_cache.get(self.project)

        # Read yaml file
        with open(inv_path) as reader:
            _contents = yaml.load(reader, Loader=yaml.SafeLoader)

        self.base_dir = _contents[0]['base_dir']
        self.contents = dict([(dset['ds_id'], dset) for dset in _contents[1:]])

    # def __contains__(self, dset):
    #     TODO:  ds_id = convert_to_ds_id(dset)
    #     return ds_id in self.contents
    # where does this fit in ?

    def get_matches(self, coll):
        # If all datasets in the collection match the inventory then 
        # return all the matching records as a dictionary of contents
        # If any dataset is not in the collection then return False
        matches = OrderedDict()

        for ds_id in coll:
            if ds_id not in self.contents:
                return False

            matches[ds_id] = self.contents[ds_id]

        return matches

    def contains(self, coll):
        # Return boolean based on whether all datasets in the collection
        # are in the inventory
        return self.get_matches(coll) is not False

    def _get_files(self, coll, prefix=''):
        # Returns an ordered dictionary of {ds_id: [file_list]}
        # If no prefix then relative paths are returned
        records = self.get_matches(coll) or []
        files = OrderedDict()

        for ds_id, record in records.items():
            rel_path = record['path']

            file_list = [os.path.join(prefix, rel_path, fname) for fname in record['files']]
            files[ds_id] = file_list

        return files

    def get_file_paths(self, coll):
        # Returns an ordered dictionary of {ds_id: [full_path_list]}
        return self._get_files(coll, prefix=self.base_dir)

    def get_file_urls(self, coll):
        # Returns an ordered dictionary of {ds_id: [file_list]}
        download_dir = CONFIG.get(f'project:{self.project}', {}).get('data_node_root') or \
            DOWNLOAD_DIR_TEMPLATE.format(project=self.project)

        return self._get_files(coll, prefix=download_dir)
