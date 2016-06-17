from matplotlib.backend_bases import FigureManagerBase
from matplotlib._pylab_helpers import Gcf


class ProxyManager(FigureManagerBase):
    """
    Helper class to remove Gfc from MultiFigureManager
    """
    def __init__(self, figure, num):
        super().__init__(figure.canvas, num)
        self.multi_manager = None
        self.figure = figure

    def show(self):
        self.multi_manager.set_active_figure(self.figure)
        self.multi_manager.show()

    def destroy(self):
        # This is called by Gcf.destroy
        self.multi_manager.remove_figure(self.figure)

    def destroy_figure(self, *args):
        # This is the callback from the gui destroy For this specific figure
        Gcf.destroy(self.num)

    def full_screen_toggle(self):
        self.multi_manager.full_screen_toggle()

    def resize(self, w, h):
        self.multi_manager.resize(w, h)

    def show_popup(self, msg):
        """
        Display message in a popup -- GUI only
        """
        pass

    def get_window_title(self):
        return self.multi_manager.get_figure_title(self.figure)

    def set_window_title(self, title):
        self.multi_manager.set_figure_title(self.figure, title)

    @property
    def toolmanager(self):
        return self.multi_manager.toolmanager

    @property
    def toolbar(self):
        return self.multi_manager.toolbar

    ##################################################
    # Extra methods because of multi manager
    def detach(self):
        self.multi_manager.detach_figure(self.figure)
