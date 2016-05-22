import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import (FigureCanvasGTK3Agg,
                                                 show)
from matplotlib.backends.backend_gtk3 import (ToolbarGTK3, StatusbarGTK3)

from matplotlib.backend_bases import FigureManagerBase

from matplotlib import verbose
from matplotlib.backend_managers import ToolManager
from matplotlib import backend_tools

import sys
from gi.repository import Gtk


class CurrentFigureManager:
    current = None

    def __init__(self):
        pass

    def __call__(self, manager=True):
        if not manager or not self.current:
            self.current = TabbedFigureManager()
        elif manager is not True:
            self.current = manager
        return self.current

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
    fm.add_figure(figure, num)
    return fm


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
        except:
            # some versions of gtk throw a glib.GError but not
            # all, so I am not sure how to catch it.  I am unhappy
            # doing a blanket catch here, but am not sure what a
            # better way is - JDH
            verbose.report('Could not load matplotlib icon: %s'
                           % sys.exc_info()[1])

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
    def num(self):
        """The num id of the active figure"""
        return self._figures[self.figure]['num']

    @property
    def figure(self):
        """Active figure"""
        return self._figure

    @property
    def canvas(self):
        """Active canvas"""
        return self._figure.canvas

    def set_figure_title(self, figure, title):
        self._figures[figure]['label'].set_text(title)

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
        del self._figures[figure]
        id_ = self._nbk.page_num(figure.canvas)
        self._nbk.remove_page(id_)
        if not self._nbk.get_n_pages():
            self.destroy()

    def detach_figure(self, figure):
        """Move figure into a new FigureManager"""
        num = self._figures[figure]['num']
        self.remove_figure(figure)
        global FM
        fm = FM(manager=False)
        fm.add_figure(figure, num)
        fm.show()
        return fm

    def add_figure(self, figure, num):
        """Add figure to this FigureManager"""
        figure.canvas.manager = self
        self._figure = figure
        self._figures[figure] = {'num': num}

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
            figure.canvas.destroy()
            self.remove_figure(figure)

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

    def destroy(self, *args):
        for figure in list(self._figures.keys()):
            figure.canvas.destroy()
            self.remove_figure(figure)
        if self._window:
            self._window.destroy()
            self._window = None

        # if Gcf.get_num_fig_managers()==0 and \
        #        not matplotlib.is_interactive() and \

        # if Gtk.main_level() >= 1:
        #     Gtk.main_quit()

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
        'set the canvas size in pixels'
        self._window.resize(width, height)
