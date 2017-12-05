import logging
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import (FigureCanvasGTK3Agg,
                                                 show)
from matplotlib.backends.backend_gtk3 import (ToolbarGTK3,
                                              StatusbarGTK3,
                                              window_icon)

from matplotlib.backend_bases import FigureManagerBase

from matplotlib.backend_managers import ToolManager
from matplotlib import backend_tools

import sys
from gi.repository import Gtk
import weakref

_log = logging.getLogger(__name__)


# This will be replaced by an rcparam
# or even better, removed when we get rid of GCF once and for all
GCF_COMPATIBLE = False
from .proxy_manager import ProxyManager


class CurrentFigureManager:
    def __init__(self):
        class Object:
            pass
        o = Object()
        self.current = weakref.ref(o)
        self.managers = set()

    def __call__(self, manager=True):

        if isinstance(manager, ProxyManager):
            manager = manager.multi_manager

        current = self.current()
        if not manager or not current or current not in self.managers:
            m = TabbedFigureManager()
        elif manager is not True:
            m = manager
        else:
            m = self.current()
        self.current = weakref.ref(m)
        self.managers.add(m)
        return m


FM = CurrentFigureManager()


def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    manager = kwargs.pop('manager', True)
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig, manager)


def new_figure_manager_given_figure(num, figure, manager):
    """
    Create a new figure manager instance for the given figure.
    """
    fm = FM(manager)
    canvas = FigureCanvasGTK3Agg(figure)
    proxy_manager = ProxyManager(figure, num)
    fm.add_figure(figure, num)
    return proxy_manager


class TabbedFigureManager(FigureManagerBase):
    """
    Public attributes

    canvas      : The FigureCanvas instance
    num         : The Figure number
    toolbar     : The Gtk.Toolbar  (gtk only)
    vbox        : The Gtk.VBox containing the canvas and toolbar (gtk only)
    window      : The Gtk.Window   (gtk only)
    """

    def __init__(self):
        self._figure = None
        self._figures = {}
        # self.key_press_handler_id = None

        self._window = Gtk.Window()
        self.set_window_title("Multi Figure")
        try:
            self._window.set_icon_from_file(window_icon)
        except (SystemExit, KeyboardInterrupt):
            # re-raise exit type Exceptions
            raise
        except Exception:
            # some versions of gtk throw a glib.GError but not
            # all, so I am not sure how to catch it.  I am unhappy
            # doing a blanket catch here, but am not sure what a
            # better way is - JDH
            _log.info('Could not load matplotlib icon: %s', sys.exc_info()[1])

        self._vbox = Gtk.Box()
        self._vbox.set_property("orientation", Gtk.Orientation.VERTICAL)
        self._window.add(self._vbox)
        self._nbk = Gtk.Notebook()
        self._nbk.connect('switch-page', self._on_switch_page)
        self._nbk.set_scrollable(True)
        self._nbk.set_show_tabs(True)
        self._vbox.pack_start(self._nbk, True, True, 0)

        self._set_tools()
        self._vbox.show_all()
        self._height = self._toolbar.size_request().height
        self._height += self._statusbar.size_request().height

        self._window.connect("destroy", self.destroy)
        self._window.connect("delete_event", self.destroy)
        if matplotlib.is_interactive():
            self._window.show()

    def _set_tools(self):
        self._toolmanager = ToolManager()
        self._toolbar = ToolbarGTK3(self._toolmanager)
        self._statusbar = StatusbarGTK3(self._toolmanager)
        backend_tools.add_tools_to_manager(self._toolmanager)
        backend_tools.add_tools_to_container(self._toolbar)
        self._vbox.pack_start(self._toolbar, False, False, 0)
        self._vbox.pack_start(Gtk.HSeparator(), False, False, 0)
        self._vbox.pack_start(self._statusbar, False, False, 0)

    @property
    def window(self):
        return self._window

    @property
    def toolmanager(self):
        return self._toolmanager

    @property
    def toolbar(self):
        return self._toolbar

    @property
    def figures(self):
        return list(self._figures.keys())

    @property
    def figure(self):
        """Active figure"""
        return self._figure

    @property
    def canvas(self):
        """Active canvas"""
        if not self._figure:
            return None
        return self._figure.canvas

    def set_figure_title(self, figure, title):
        self._figures[figure]['label'].set_text(title)

    def get_figure_title(self, figure):
        return self._figures[figure]['label'].get_text()

    def _on_switch_page(self, holder, canvas, page):
        if canvas is not self.canvas:
            self.set_active_figure(canvas.figure)

    def set_active_figure(self, figure):
        """Set the active figure"""
        if figure not in self._figures:
            raise ValueError("Figure not managed by this manager")
        self._figure = figure
        self._toolmanager.set_figure(figure)
        id_ = self._nbk.page_num(self.canvas)
        self._nbk.set_current_page(id_)
        self._nbk.show()

    def remove_figure(self, figure):
        """Remove figure from this FigureManager"""
        figure.multi_manager = None

        if figure is self._figure:
            self._figure = None

        del self._figures[figure]
        id_ = self._nbk.page_num(figure.canvas)
        self._nbk.remove_page(id_)
        if not self._nbk.get_n_pages():
            self.destroy_window()

    def detach_figure(self, figure):
        """Move figure into a new FigureManager"""

        num = self._figures[figure]['manager'].num
        self.remove_figure(figure)

        global FM
        fm = FM(manager=False)
        fm.add_figure(figure, num)
        fm.show()
        return fm

    def add_figure(self, figure, num):
        """Add figure to this FigureManager"""
        self._figure = figure
        self._figures[figure] = {}

        figure.canvas.manager.multi_manager = self
        self._figures[figure]['manager'] = figure.canvas.manager

        title = 'Fig %d' % num
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.HORIZONTAL)
        box.set_spacing(5)

        label = Gtk.Label(title)
        box.pack_start(label, True, True, 0)
        self._figures[figure]['label'] = label

        # close button
        button = Gtk.Button()
        button.set_tooltip_text('Close')
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_focus_on_click(False)
        button.add(Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE,
                                            Gtk.IconSize.MENU))
        box.pack_end(button, False, False, 0)

        def _remove(btn, figure):
            self.destroy_figure(figure)

        button.connect("clicked", _remove, figure)

        # Detach button
        button = Gtk.Button()
        button.set_tooltip_text('Detach')
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_focus_on_click(False)
        button.add(Gtk.Image.new_from_stock(Gtk.STOCK_JUMP_TO,
                                            Gtk.IconSize.MENU))
        box.pack_end(button, False, False, 0)

        def _detach(btn, figure):
            self.detach_figure(figure)
        button.connect("clicked", _detach, figure)

        box.show_all()
        figure.canvas.show()
        self._nbk.append_page(figure.canvas, box)
        self.set_active_figure(figure)

        figure.canvas.grab_focus()
        self._toolmanager.set_figure(self.figure)
        w = int(figure.bbox.width)
        h = self._height + int(figure.bbox.height)
        h += self._nbk.size_request().height
        self._window.set_default_size(w, h)
        self.resize(w, h)

    def destroy_figure(self, figure):
        figure.canvas.destroy()
        self._figures[figure]['manager'].destroy_figure()
        # This will come back in remove_figure

    def destroy(self, *args):
        for figure in list(self._figures.keys()):
            self.destroy_figure(figure)

    def destroy_window(self, *args):
        # This method is not to be called directly
        # only from remove_figure if there are no more figures
        if self._window:
            self._window.destroy()
            self._window = None

        FM.managers.remove(self)
        if len(FM.managers) == 0 and not matplotlib.is_interactive() and \
            Gtk.main_level() >= 1:
            Gtk.main_quit()

    def show(self):
        self._window.show()

    def full_screen_toggle(self):
        self._full_screen_flag = not self._full_screen_flag
        if self._full_screen_flag:
            self._window.fullscreen()
        else:
            self._window.unfullscreen()
    _full_screen_flag = False

    def get_window_title(self):
        return self._window.get_title()

    def set_window_title(self, title):
        self._window.set_title(title)

    def resize(self, width, height):
        self._window.resize(width, height)
