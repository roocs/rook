from urllib.parse import urlparse

from pywps.inout.outputs import MetaFile, MetaLink4
from pywps import FORMATS

file_type_map = {"NetCDF": FORMATS.NETCDF}


def build_metalink(identity, description, workdir, file_uris, file_type="NetCDF"):
    ml4 = MetaLink4(identity, description, workdir=workdir)
    file_desc = f"{file_type} file"

    # Add file paths or URLs
    for file_uri in file_uris:
        mf = MetaFile(file_desc, file_desc, fmt=file_type_map.get(file_type, file_type))

        if urlparse(file_uri).scheme in ["http", "https"]:
            mf.url = file_uri
        else:
            mf.file = file_uri

        ml4.append(mf)

    return ml4
