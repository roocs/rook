

class GetFiles:
    def __init__(self, operation, collection, kwargs):
        self.operation = operation
        self.collection = collection
        self.kwargs = kwargs
        # probably needs to take operation e.g. subset and kwargs related to this

    def quality_controlled(self):
        # check it exists using inventory class (use inventory class)
        pass

    def is_characterised(self):
        # check it is characterised using characterised class in daops (move that to here?)
        pass

    def find_fixes(self):
        # find fixes - to see if there are any! (use Fixer class)
        pass

    def get_files(self):
        # goes through decision logic and then calls correct function - either through daops or URL constructor
        # will be called by rook wps process

        # what happens with orchestrate - always WPS generated files

        # maybe this needs to be a separate class?
        pass
