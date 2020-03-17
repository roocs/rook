import tempfile
import daops


class Operator(object):
    def __init__(self, data_root_dir, output_dir):
        self.config = {
            'data_root_dir': data_root_dir,
            'output_dir': output_dir,
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

    def call(self, args, data_refs):
        raise NotImplementedError("implemented in subclass")


class Subset(Operator):
    def call(self, args):
        kwargs = {}
        if 'time' in args:
            kwargs['time'] = args['time'].split('/')
        if 'space' in args:
            kwargs['space'] = [float(item) for item in args['space'].split(',')]
        if 'data_ref' in args:
            kwargs['data_refs'] = args['data_ref']
        kwargs.update(self.config)
        kwargs['output_dir'] = tempfile.mkdtemp(dir=self.config['output_dir'], prefix='subset_')
        result = daops.subset(
            **kwargs,
        )
        return result.file_paths


class Average(Operator):
    def call(self, args):
        return args['data_ref']


class Diff(Operator):
    def call(self, args):
        return args['data_ref_a']
