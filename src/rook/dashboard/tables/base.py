from bokeh.embed import components

from ..base import BaseView


class TableView(BaseView):
    def table(self):
        raise NotImplementedError

    def components(self):
        return components(self.table())
