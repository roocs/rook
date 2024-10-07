class BaseView:
    def __init__(self, df):
        self.df = df

    def data(self):
        raise NotImplementedError
