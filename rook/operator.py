import tempfile


class Operator(object):
    def __init__(self, base_dir, output_dir):
        self.config = {
            'base_dir': base_dir,
            'output_dir': output_dir,
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

    def call(self, args, collection):
        raise NotImplementedError("implemented in subclass")


class Subset(Operator):
    def call(self, args):
        # TODO: handle lazy load of daops
        from daops.ops import subset
        kwargs = {}
        if 'time' in args:
            kwargs['time'] = args['time'].split('/')
        if 'area' in args:
            kwargs['area'] = [float(item) for item in args['area'].split(',')]
        if 'collection' in args:
            kwargs['collection'] = args['collection']
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
        return args['data_ref_a']
