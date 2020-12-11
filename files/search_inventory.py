import urllib.request


class Inventory:
    def __init__(self, project):
        self.project = project
        self.inventory_url = f"https://raw.githubusercontent.com/cp4cds/c3s_34g_manifests" \
                             f"/add_inventories/inventories/{self._project}/{self._project}_files_latest.yml"

    def open_inventory(self):
        file = urllib.request.urlopen(self.inventory_url)
        dict_list = yaml.load(file)
        return dict_list

    def dataset_exists(self, dset):
        # need to convert dset to ds_id format
        # ds_id = convert_to_ds_id(dset)
        ds_id = dset
        dict_list = self.open_inventory()
        return ds_id, any(d['ds_id'] == ds_id for d in dict_list[1:])


class BuildURL(Inventory):
    def __init__(self, project, collection):
        super().__init__(project)
        self.collection = collection
        self.file_url_prefix = f"https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_{self.project}/"

    def get_file_list(self, ds_id):
        dict_list = self.open_inventory()
        for d in dict_list:
            if d['ds_id'] == ds_id:
                path = d['path']
                files = d['files']
                return dict(path=path, files=files)
            else:
                raise Exception(f"Cannot find dataset {ds_id}")

    def construct_urls(self, ds_id):
        path, files = self.get_file_list(ds_id)
        path = path.split('/')[1:].join('/')
        file_urls = []
        for file in files:
            url = self.file_url_prefix + path + file
            file_urls.append(url)
        return file_urls

    # def collection_urls(self):
    #     # url list is a list of lists
    #     url_list = []
    #
    #     for dset in self.collection:
    #         # ds_id = convert_to_ds_id(dset)
    #         ds_id = dset
    #         url_list.append(self.construct_urls(ds_id))



