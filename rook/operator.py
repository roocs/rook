import os
import tempfile
from copy import deepcopy

from rook.director import wrap_director
from rook.utils.input_utils import resolve_input
from rook.utils.average_utils import run_average
from rook.utils.subset_utils import run_subset


class Operator(object):
    # Sub-classes require "prefix" property
    prefix = NotImplemented

    def __init__(self, output_dir, apply_fixes=True):
        self.config = {
            "output_dir": output_dir,
            # 'apply_fixes': apply_fixes
            # 'original_files': original_files
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

    def call(self, args):
        args.update(self.config)
        args["output_dir"] = self._get_output_dir()
        collection = args["collection"]  # collection is a list

        runner = self._get_runner()

        # Quick hack to find out if collection is a list of files
        if os.path.isfile(collection[0]):  # should this check something else?
            kwargs = deepcopy(args)
            kwargs["collection"] = resolve_input(args.get("collection"))
            output_uris = runner(kwargs)
        else:
            # Setting "original_files" to False, to force use of WPS in a workflow
            args["original_files"] = False  # think this can be removed?
            director = wrap_director(collection, args, runner)
            output_uris = director.output_uris

            # In rook.operator, within the `Operator.call()` function, we need...
            #
            # NOTE: output_uris might be file paths OR URLs
            #  If they are URLs: then any subsequent Operators will need to download them
            #  How will we do that?
            #  In daops.utils.consolidate:
            #   - run a single:  `collection = consolidate_collection(collection)`
            #     - it would group a sequence of items into:
            #       1. dataset ids (from individual ids and/or id patterns)
            #       2. URLs to individual NC files
            #         - analyse URLs and compare path and file names,
            #           - if path and relevant parts of file name are the same:
            #               - group by inferred dataset in separate directories
            #         - implement by: 1. strip the last component of files
            #                         2. create collection object to group them
            #                         3. download them into directories related to collection
            #       3. Directories
            #       4. File paths:
            #         - Group by common directory()
            #         - so that xarray will attempt to aggregate them
            #
            #   - then call the existing consolidate code that loops through each _dset_
            #
        return output_uris

    def _get_runner(self):
        return NotImplementedError

    def _get_output_dir(self):
        return tempfile.mkdtemp(dir=self.config["output_dir"], prefix=f"{self.prefix}_")


class Subset(Operator):
    prefix = "subset"

    def _get_runner(self):
        return run_subset


class Average(Operator):
    prefix = "average"

    def _get_runner(self):
        return run_average


Diff = Average
