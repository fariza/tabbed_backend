FM = None
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



def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig)

def new_figure_manager_given_figure(num, figure):
    """
    Create a new figure manager instance for the given figure.
    """
    global FM
    if FM is None:
        FM = TabbedFigureManager()
    canvas = FigureCanvasGTK3Agg(figure)
    manager = FM.add_canvas(canvas, num)
    return FM



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
        self._canvas = None
        self._num = None
        self._canvases = {}
        self.key_press_handler_id = None

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
            verbose.report('Could not load matplotlib icon: %s' % sys.exc_info()[1])

        self._vbox = Gtk.Box()
        self._vbox.set_property("orientation", Gtk.Orientation.VERTICAL)
        self._window.add(self._vbox)
        self._nbk = Gtk.Notebook()
        self._nbk.connect('switch-page', self._on_switch_page)
        self._vbox.pack_start(self._nbk, True, True, 0)

        self._set_tools()
        self._vbox.show_all()

        self._height = self._vbox.size_request().height
        self._window.connect("destroy", self.destroy)
        self._window.connect("delete_event", self.destroy)

    def _set_tools(self):
        self._toolmanager = ToolManager(self)
        self._toolbar = ToolbarGTK3(self._toolmanager)
        backend_tools.add_tools_to_manager(self._toolmanager)
        backend_tools.add_tools_to_container(self._toolbar)
        self._statusbar = StatusbarGTK3(self._toolmanager)
        self._vbox.pack_start(self._toolbar, False, False, 0)
        self._vbox.pack_start(Gtk.HSeparator(), False, False, 0)
        self._vbox.pack_start(self._statusbar, False, False, 0)

    @property
    def num(self):
        return self._num

    @property
    def canvas(self):
        return self._canvas

    def _on_switch_page(self, holder, canvas, page):
        if canvas is not self.canvas:
            self.set_active_canvas(canvas)

    def set_active_canvas(self, canvas):
        self._canvas = canvas
        self._toolmanager.set_figure(canvas.figure)
        id_ = self._nbk.page_num(canvas)
        self._nbk.set_current_page(id_)
        self._nbk.show()

    def remove_canvas(self, canvas):
        del self._canvases[canvas]
        id_ = self._nbk.page_num(canvas)
        self._nbk.remove_page(id_)
        canvas.destroy()
        if not self._nbk.get_n_pages():
            self.destroy()

    def add_canvas(self, canvas, num):
        canvas.manager = self
        self._canvas = canvas
        self._num = num
        self._canvases[canvas] = {'num': num}

        title = 'Fig %d' % num
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.HORIZONTAL)
        box.set_spacing(5)

        label = Gtk.Label(title)
        box.pack_start(label, True, True, 0)
        self._canvases[canvas]['label'] = label

        # close button
        button = Gtk.Button()
        button.set_tooltip_text('Close')
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_focus_on_click(False)
        button.add(Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE,
                                            Gtk.IconSize.MENU))
        box.pack_end(button, False, False, 0)

        def _remove(btn, canvas):
            self.remove_canvas(canvas)

        button.connect("clicked", _remove, canvas)

        # # Detach button
        # button = Gtk.Button()
        # button.set_tooltip_text('Detach')
        # button.set_relief(Gtk.ReliefStyle.NONE)
        # button.set_focus_on_click(False)
        # button.add(Gtk.Image.new_from_stock(Gtk.STOCK_JUMP_TO,
        #                                     Gtk.IconSize.MENU))
        # box.pack_end(button, False, False, 0)
        #
        # def _detach(btn, canvas):
        #     return self.remove_canvas(canvas)
        # button.connect("clicked", _detach, canvas)

        box.show_all()
        canvas.show()
        self._nbk.append_page(canvas, box)
        self.set_active_canvas(canvas)

        #
        # self.canvas.grab_focus()
        self._toolmanager.set_figure(self.canvas.figure)
        w = int(canvas.figure.bbox.width)
        h = int(canvas.figure.bbox.height)
        self._window.set_default_size (w, self._height + h)


    def destroy(self, *args):
        for canvas in list(self._canvases.keys()):
            self.remove_canvas(canvas)
        if self._window:
            self._window.destroy()
            self._window = None

        # if Gcf.get_num_fig_managers()==0 and \
        #        not matplotlib.is_interactive() and \

        if Gtk.main_level() >= 1:
            Gtk.main_quit()

    def show(self):
        self._window.show()

    def full_screen_toggle (self):
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
