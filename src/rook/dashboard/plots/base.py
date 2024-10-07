from bokeh.embed import components

from ..base import BaseView


class PlotView(BaseView):
    def plot(self):
        raise NotImplementedError

    def components(self):
        return components(self.plot())
