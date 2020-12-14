import os
import yaml

from rook.director.inv_cache import InventoryCache, inventory_cache

dummy_inv_cache = None
dummy_inv_dir = '/tmp/test-inventory-cache'


def setup_module():
    global dummy_inv_cache
    dummy_inv_cache = InventoryCache(dummy_inv_dir)


def test_inventory_cache_exists():
    assert(isinstance(inventory_cache, InventoryCache))


def test_dummy_inventory_cache_exists():
    assert(isinstance(dummy_inv_cache, InventoryCache))


def test_inventory_cache_exists():
    dummy_inv_cache.get('cmip6')

    #TODO: Work out a way to dynamically find the above file
    inv_path = os.path.join(dummy_inv_dir, 'c3s-cmip6_files_v20201201.yml')

    with open(inv_path) as reader:
        inv = yaml.load(reader)

    assert(len(inv) == 1590)
    assert(inv[0]['project'] == 'c3s-cmip6')


def teardown_module():
    for f in os.listdir(dummy_inv_dir):
        fpath = os.path.join(dummy_inv_dir, f)
        os.remove(fpath)

    os.rmdir(dummy_inv_dir)