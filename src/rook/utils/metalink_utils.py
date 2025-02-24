from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pathlib import Path


from pywps import FORMATS
from pywps.inout.outputs import MetaFile, MetaLink4

file_type_map = {"NetCDF": FORMATS.NETCDF}


def build_metalink(identity, description, workdir, file_uris, file_type="NetCDF"):
    ml4 = MetaLink4(identity, description, workdir=workdir)
    file_desc = f"{file_type} file"

    # Add file paths or URLs
    for file_uri in file_uris:
        mf = MetaFile(file_desc, file_desc, fmt=file_type_map.get(file_type, file_type))

        if urlparse(file_uri).scheme in ["http", "https"]:
            mf.url = file_uri
            # TODO: size calculation takes too long. Set size from inventory/catalog.
            mf.size = 0
        else:
            mf.file = file_uri

        ml4.append(mf)

    return ml4


def extract_paths_from_metalink(path):
    path = path.replace("file://", "")
    xml = Path(path).open().read()
    return parse_metalink(xml)


def parse_metalink(xml):
    doc = BeautifulSoup(xml, "xml")
    paths = [el.text.replace("file://", "") for el in doc.find_all("metaurl")]
    return paths
