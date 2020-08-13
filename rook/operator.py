import tempfile

from roocs_utils.parameter import parameterise

class Operator(object):
    def __init__(self, project, output_dir):
        self.config = {
            'project': project,
            'output_dir': output_dir,
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

    def call(self, args, collection):
        raise NotImplementedError("implemented in subclass")


class Subset(Operator):
    def call(self, args):
        # TODO: handle lazy load of daops
        from daops.ops.subset import subset
        kwargs = parameterise.parameterise_rook(collection=args.get('collection'),
                                                time=args.get('time'),
                                                level=args.get('level'),
                                                area=args.get('area'))
        kwargs.update(self.config)
        kwargs['output_dir'] = tempfile.mkdtemp(dir=self.config['output_dir'], prefix='subset_')
        result = subset(
            **kwargs,
        )
        return result.file_paths


class Average(Operator):
    def call(self, args):
        return args['collection']


class Diff(Operator):
    def call(self, args):
        return args['collection_a']
