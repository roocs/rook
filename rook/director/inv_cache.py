import os
import requests

from roocs_utils import CONFIG


INVENTORY_URL_TEMPLATE = "https://raw.githubusercontent.com/cp4cds/c3s_34g_manifests" \
                         "/master/inventories/{project}/{project}_files_latest.yml"


class InventoryCache:

    def __init__(self, cache_dir='/tmp/inventory_cache'):
        self.cache_dir = cache_dir
        self.content = {}

        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        self._load_content()

    def _get_project_id(self, fname):
        return fname.split('_')[0]

    def _load_content(self):
        # Search the cache directory for files and put in self.content
        for fname in os.listdir(self.cache_dir):
            self.content[self._get_project_id(fname)] = os.path.join(self.cache_dir, fname)

    def _download(self, project):
        default_inv_url = INVENTORY_URL_TEMPLATE.format(project=project)

        # Get the file the symlink points to first
        symlink_url = CONFIG.get(f'[project:{project}', {}).get('inventory_url', default_inv_url)
        inv_name = requests.get(symlink_url).text.strip()

        if inv_name in self.content:
            # If already got, take no action
            return 
        
        # Download the real file
        inventory_url = os.path.join(os.path.dirname(inventory_url), inv_name) # should this be inventory_url or something else?
        resp = request.get(inventory_url)

        # Write to cache file
        cache_file = os.path.join(self.cache_dir, inv_name)
        with open(cache_file, 'w') as writer:
            writer.write(resp)

        self.content[project] = cache_file

    def get(self, project):
        if project not in self.content:
            self._download(project)
        
        return self.content[project]


# Define a single global inventory cache object
inventory_cache = InventoryCache()
