import os
import tempfile
from copy import deepcopy
import pathlib

from rook.director import wrap_director
from rook.utils.input_utils import resolve_to_file_paths
from rook.utils.average_utils import (
    run_average_by_time,
    run_average_by_dim,
    run_weighted_average,
    run_average_by_shape,
)
from rook.utils.subset_utils import run_subset
from rook.utils.concat_utils import run_concat
from rook.utils.regrid_utils import run_regrid
from roocs_utils.utils.file_utils import is_file_list, FileMapper


class Operator(object):
    # Sub-classes require "prefix" property
    prefix = NotImplemented

    def __init__(self, output_dir):
        if isinstance(output_dir, pathlib.Path):
            output_dir_ = output_dir.as_posix()
        else:
            output_dir_ = output_dir
        self.config = {
            "output_dir": output_dir_,
            # "apply_fixes": apply_fixes,
            # 'original_files': original_files
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

    def call(self, args):
        # args.update(self.config)
        args["output_dir"] = self._get_output_dir()
        collection = args["collection"]  # collection is a list

        runner = self._get_runner()

        if is_file_list(collection):
            # This block is called if this is NOT the first stage of a workflow, and
            # the collection will be a file list (one or more files)
            args["apply_fixes"] = False
            kwargs = deepcopy(args)
            file_paths = resolve_to_file_paths(args.get("collection"))
            kwargs["collection"] = FileMapper(file_paths)
            output_uris = runner(kwargs)  # this needs to be in a list
        else:
            # This block is called when this is the first stage of a workflow
            director = wrap_director(collection, args, runner)
            output_uris = director.output_uris

        return output_uris

    def _get_runner(self):
        return NotImplementedError

    def _get_output_dir(self):
        return tempfile.mkdtemp(dir=self.config["output_dir"], prefix=f"{self.prefix}_")


class Subset(Operator):
    prefix = "subset"

    def _get_runner(self):
        return run_subset


class AverageByTime(Operator):
    prefix = "average_time"

    def _get_runner(self):
        return run_average_by_time


class AverageByDimension(Operator):
    prefix = "average"

    def _get_runner(self):
        return run_average_by_dim


class AverageByShape(Operator):
    prefix = "average_shape"

    def _get_runner(self):
        return run_average_by_shape



class WeightedAverage(Operator):
    prefix = "weighted_average"

    def _get_runner(self):
        return run_weighted_average


class Regrid(Operator):
    prefix = "regrid"

    def _get_runner(self):
        return run_regrid


class Concat(Operator):
    prefix = "concat"

    def _get_runner(self):
        return run_concat
