import requests
import shutil
from lxml import etree
import xarray as xr


def download_file(url, tmp_path):
    # use tmp_path (pathlib.Path) from pytest:
    # https://docs.pytest.org/en/stable/tmpdir.html
    local_filename = url.split("/")[-1]
    p = tmp_path / local_filename
    with requests.get(url, stream=True) as r:
        with p.open(mode="wb") as f:
            shutil.copyfileobj(r.raw, f)
    return p.as_posix()


def open_dataset(url, tmp_path):
    ds = xr.open_dataset(download_file(url, tmp_path), use_cftime=True)
    return ds


def parse_metalink(xml):
    xml_ = xml.replace(' xmlns="', ' xmlnamespace="')
    tree = etree.fromstring(xml_.encode())
    urls = [m.text for m in tree.xpath("//metaurl")]
    return urls
