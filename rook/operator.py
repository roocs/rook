import os
import tempfile


def _resolve_collection_if_files(outputs):
    # If multiple outputs are files with a common directory name, then
    # return that as a single output

    if len(outputs) > 1:
        first_dir = os.path.dirname(outputs[0])

        if all([os.path.isfile(output) for output in outputs]):
            if os.path.dirname(os.path.commonprefix(outputs)) == first_dir:
                return first_dir

    return outputs[0]


class Operator(object):
    def __init__(self, output_dir, apply_fixes=True):
        self.config = {
            "output_dir": output_dir,
            # 'apply_fixes': apply_fixes
            # 'original_files': original_files
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

    def call(self, args, collection):
        raise NotImplementedError("implemented in subclass")


class Subset(Operator):
    def call(self, args):
        # Convert file list to directory if required
        collection = _resolve_collection_if_files(args.get("collection"))

        # TODO: handle lazy load of daops
        from daops.ops.subset import subset

        # from .tweaks import subset
        kwargs = dict(
            collection=collection,
            time=args.get("time"),
            level=args.get("level"),
            area=args.get("area"),
            apply_fixes=args.get("apply_fixes"),
        )
        kwargs.update(self.config)
        kwargs["output_dir"] = tempfile.mkdtemp(
            dir=self.config["output_dir"], prefix="subset_"
        )
        result = subset(
            **kwargs,
        )
        return result.file_uris


class Average(Operator):
    def call(self, args):
        return args["collection"]


class Diff(Operator):
    def call(self, args):
        return args["collection_a"]
