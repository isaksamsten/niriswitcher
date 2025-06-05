import logging
import time

from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Pango

from ._anim import ease_in_out_cubic, ease_out_cubic
from ._wm import Window, Workspace

from ._config import config

logger = logging.getLogger(__name__)


class ApplicationView(Gtk.Box):
    """
    A custom GTK Box widget representing an application view with an icon and name label.

    This class displays an application's icon and name within a vertical box layout.
    It provides methods to visually indicate selection and focus states.

    Attributes:
        window (Window): The window instance associated with this application view.

    Args:
        window (Window): The window object representing the application.
        size: The size to be used for the application icon.
    """

    __gsignals__ = {
        "enter": (GObject.SignalFlags.RUN_FIRST, None, (Window,)),
        "leave": (GObject.SignalFlags.RUN_FIRST, None, (Window,)),
        "released": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (Gtk.GestureClick, int, Window),
        ),
    }

    def __init__(self, window: Window, *, size: int) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        icon = new_app_icon_or_default(window.app_info, size)
        name = Gtk.Label()
        name.set_ellipsize(Pango.EllipsizeMode.END)
        name.set_max_width_chars(1)
        name.set_hexpand(True)
        if self.window.name:
            name.set_label(self.window.name)

        self.append(icon)
        self.append(name)

        self.add_css_class("application")
        name.add_css_class("application-name")
        icon.add_css_class("application-icon")
        self.set_urgent(window.is_urgent)

        gesture = Gtk.GestureClick.new()
        gesture.set_button(0)
        gesture.connect("released", self.on_release)
        motion = Gtk.EventControllerMotion.new()
        motion.connect("enter", self.on_enter)
        motion.connect("leave", self.on_leave)
        self.connect("unmap", self.on_unmap)
        self.connect("map", self.on_map)
        self.add_controller(motion)
        self.add_controller(gesture)

    def on_map(self, widget):
        self._urgency_handler_id = self.window.connect(
            "notify::is-urgent", self.on_urgency_change
        )

    def on_unmap(self, widget):
        self.window.disconnect(self._urgency_handler_id)

    def on_urgency_change(self, window, spec):
        self.set_urgent(window.get_property(spec.name))

    def on_release(
        self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float
    ) -> None:
        self.emit("released", gesture, n_press, self.window)

    def on_enter(self, motion: Gtk.EventControllerMotion, x: float, y: float) -> None:
        self.emit("enter", self.window)

    def on_leave(self, motion: Gtk.EventControllerMotion) -> None:
        self.emit("leave", self.window)

    def set_urgent(self, is_urgent):
        if is_urgent:
            self.add_css_class("urgent")
        else:
            self.remove_css_class("urgent")

    def select(self) -> None:
        self.add_css_class("selected")

    def deselect(self) -> None:
        self.remove_css_class("selected")

    def focus(self) -> None:
        self.add_css_class("focused")

    def unfocus(self) -> None:
        self.remove_css_class("focused")


def new_app_icon_or_default(app_info: Gio.DesktopAppInfo, size):
    """
    Returns a Gtk.Image widget for the given application's icon or a default
    icon if unavailable.

    Attempts to retrieve the icon from the provided Gio.DesktopAppInfo object.
    Handles themed icons, loadable icons, and string icon names. If no suitable
    icon is found, falls back to the "application-x-executable" icon or an
    empty Gtk.Image.

    Args:
        app_info (Gio.DesktopAppInfo): The application info object containing icon data.
        size (int): The desired pixel size for the icon image.

    Returns:
        Gtk.Image: A Gtk.Image widget displaying the application's icon or a default icon.
    """
    icon_name = ""
    if app_info:
        icon = app_info.get_icon()
        if isinstance(icon, Gio.ThemedIcon):
            icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            icon_names = icon.get_names()
            for icon_name in icon_names:
                if icon_theme.has_icon(icon_name):
                    try:
                        gicon = Gio.ThemedIcon.new(icon_name)
                        image = Gtk.Image.new_from_gicon(gicon)
                        image.set_pixel_size(size)
                        return image
                    except Exception:
                        continue
        elif isinstance(icon, Gio.LoadableIcon):
            try:
                image = Gtk.Image.new_from_gicon(icon)
                image.set_pixel_size(size)
                return image
            except Exception:
                pass
        elif isinstance(icon, str):
            if icon_theme.has_icon(icon):
                try:
                    gicon = Gio.ThemedIcon.new(icon)
                    image = Gtk.Image.new_from_gicon(gicon)
                    image.set_pixel_size(size)
                    return image
                except Exception:
                    pass

    icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    if icon_theme.has_icon("application-x-executable"):
        logger.debug("Can't find icon for %s, using default fallback", icon_name)
        gicon = Gio.ThemedIcon.new("application-x-executable")
        image = Gtk.Image.new_from_gicon(gicon)
        image.set_pixel_size(size)
        return image

    logger.error("Can't find icon for %s, using empty image", icon_name)
    image = Gtk.Image()
    image.set_pixel_size(size)
    return image


class AnimateScrollToWidget:
    """
    Animates scrolling of a Gtk.ScrolledWindow to bring a specified widget into
    view smoothly.

    This class provides a callable object that, when invoked with a widget,
    scrolls the associated Gtk.ScrolledWindow horizontally to center the widget
    within the visible area. The scrolling animation duration can be
    customized.

    Attributes:
        scrolled_window (Gtk.ScrolledWindow): The scrolled window to animate.
        _timer_id (int or None): The identifier for the active GLib timeout, if any.

    Example:
        animator = AnimateScrollToWidget(scrolled_window)
        animator(target_widget, duration=300)

    """

    def __init__(self, *, duration=200, easing=None):
        self._timer_id = None
        self.duration = duration
        self.easing = easing

    def __call__(self, scrolled_window, widget):
        easing = self.easing
        if easing is None:
            easing = ease_in_out_cubic

        def animate_scroll_to_application():
            hadj = scrolled_window.get_hadjustment()
            child_x = widget.get_allocation().x
            child_width = widget.get_allocation().width
            visible_start = hadj.get_value()
            visible_end = visible_start + hadj.get_page_size()
            if child_x >= visible_start and (child_x + child_width) <= visible_end:
                return

            child_center = child_x + child_width / 2
            new_value = child_center - hadj.get_page_size() / 2

            new_value = max(
                hadj.get_lower(),
                min(new_value, hadj.get_upper() - hadj.get_page_size()),
            )

            if self.duration == 0:
                hadj.set_value(new_value)
                self._timer_id = None
                return

            start_value = hadj.get_value()
            delta = new_value - start_value
            start_time = time.monotonic()

            def animate_scroll():
                elapsed = (time.monotonic() - start_time) * 1000
                t = min(elapsed / self.duration, 1.0)
                eased_t = easing(t)
                current_value = start_value + delta * eased_t
                hadj.set_value(current_value)
                if t < 1.0:
                    return True
                else:
                    self._timer_id = None
                    hadj.set_value(new_value)
                    return False

            if self._timer_id is not None:
                GLib.source_remove(self._timer_id)
                self._timer_id = None

            self._timer_id = GLib.timeout_add(16, animate_scroll)

        GLib.idle_add(animate_scroll_to_application)


class WidgetPropertyAnimation:
    def __init__(
        self, method, *, before, setter, initial, target, duration=200, easing=None
    ):
        self._timer_id = None
        self.initial = initial
        self.target = target
        self._current = None
        self.method = method
        self.setter = setter
        self.before = before
        self.duration = duration
        self.easing = easing

    def __call__(self, *args, **kwargs):
        before = self.before(*args, **kwargs)
        if hasattr(self.duration, "__call__"):
            duration = self.duration(*args, **kwargs)
        else:
            duration = self.duration

        if not before:
            initial, target = self.target, self.initial
        else:
            initial = self.initial
            target = self.target

        self._current = initial
        easing = self.easing
        if easing is None:
            easing = ease_out_cubic

        if duration == 0:
            self.setter(target)
            self.method(*args, **kwargs)
            return

        if before:
            self.setter(initial)
            self.method(*args, **kwargs)

        def idle_add():
            delta = target - initial
            start_time = time.monotonic()

            def do_animation():
                elapsed = (time.monotonic() - start_time) * 1000
                t = min(elapsed / duration, 1.0)
                eased_t = easing(t)
                self._current = initial + delta * eased_t
                if t < 1.0:
                    self.setter(self._current)
                    return True
                else:
                    self._timer_id = None
                    self._current = None
                    self.setter(target)
                    if not before:
                        self.method(*args, **kwargs)
                    return False

            if self._timer_id is not None:
                GLib.source_remove(self._timer_id)

            self._timer_id = GLib.timeout_add(16, do_animation)

        GLib.idle_add(idle_add)


class SizeTransition:
    """
    Handles smooth size transitions for a widget over a specified duration using cubic easing.

    This class manages the animation of a widget's size from an initial value to a target value,
    updating the size incrementally and triggering widget redraws as needed.

    Attributes:
        _timer_id (int or None): ID of the active GLib timeout source, or None if no animation is running.
        current_size (float or None): The current interpolated size during the transition, or None when idle.
        widget: The widget instance whose size is being animated.

    Example:
        transition = SizeTransition(widget)
        transition(initial_size=100, target_size=200, duration=300)
    """

    def __init__(self, *, duration=200, easing=None):
        self._timer_id = None
        self.current_size = None
        self.duration = duration
        self.easing = easing

    def __call__(self, widget, initial_size, target_size):
        self.current_size = initial_size
        easing = self.easing
        if easing is None:
            easing = ease_out_cubic

        if self.duration == 0:
            self.current_size = target_size
            return

        def idle_add():
            delta = target_size - initial_size
            start_time = time.monotonic()

            def do_animation():
                elapsed = (time.monotonic() - start_time) * 1000
                t = min(elapsed / self.duration, 1.0)
                eased_t = easing(t)
                self.current_size = initial_size + delta * eased_t
                if t < 1.0:
                    widget.queue_resize()
                    return True
                else:
                    self._timer_id = None
                    self.current_size = None
                    widget.queue_resize()
                    return False

            if self._timer_id is not None:
                GLib.source_remove(self._timer_id)

            self._timer_id = GLib.timeout_add(16, do_animation)

        GLib.idle_add(idle_add)


class WorkspaceView(Gtk.ScrolledWindow):
    __gsignals__ = {
        "selection-changed": (GObject.SignalFlags.RUN_FIRST, None, (Window,)),
        "focus-requested": (GObject.SignalFlags.RUN_FIRST, None, (Window, bool)),
        "close-requested": (GObject.SignalFlags.RUN_FIRST, None, (Window,)),
    }

    def __init__(
        self, workspace, windows, *, min_width=600, max_width=800, icon_size=128
    ):
        super().__init__()
        self.application_views = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=12
        )
        self.add_css_class("workspace")
        self.workspace = workspace
        self.application_views.set_halign(Gtk.Align.CENTER)
        self.application_views.set_valign(Gtk.Align.CENTER)
        self.application_views.set_hexpand(False)
        self.application_views.set_homogeneous(True)
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_child(self.application_views)
        for window in windows:
            application_view = ApplicationView(window, size=icon_size)
            application_view.connect("enter", self.on_enter)
            application_view.connect("leave", self.on_leave)
            application_view.connect("released", self.on_released)
            self.application_views.append(application_view)

        self.max_width = max_width
        self.min_width = min_width
        self.size_transition = SizeTransition()
        self._scroll_to = AnimateScrollToWidget()
        self.current_application = self.get_initial_selection()
        self.scroll_duration = 200
        self.resize_duration = 200
        self.resize_easing = None
        self.scroll_easing = None

    def set_width(self, min_width, max_width):
        self.max_width = max_width
        self.min_width = min_width
        self.queue_resize()

    def on_released(self, widget, gesture, n_press, window):
        hide = True
        if config.general.double_click_to_hide:
            hide = n_press > 1

        button = gesture.get_current_button()
        if button == 1:
            self.emit("focus-requested", window, hide)
        elif button == 3:
            self.emit("close-requested", window)

    def on_enter(self, widget, window):
        if widget is not self.current_application:
            widget.select()
            self.emit("selection-changed", window)

    def on_leave(self, widget, window):
        if widget is not self.current_application:
            widget.deselect()

        if self.current_application is not None:
            self.emit("selection-changed", self.current_application.window)

    def get_first_application_view(self):
        return self.application_views.get_first_child()

    def get_last_application_view(self):
        return self.application_views.get_last_child()

    def is_empty(self):
        return self.application_views.get_first_child() is None

    def set_scroll_duration(self, scroll_duration):
        self._scroll_to.duration = scroll_duration

    def set_resize_duration(self, resize_duration):
        self.size_transition.duration = resize_duration

    def set_resize_easing(self, easing):
        self.size_transition.easing = easing

    def set_scroll_easing(self, easing):
        self._scroll_to.easing = easing

    def get_initial_selection(self):
        return self.get_first_application_view()

    def scroll_to(self, widget):
        self._scroll_to(self, widget)

    def focus_current(self, hide=True):
        if self.current_application is not None:
            self.emit("focus-requested", self.current_application.window, hide)

    def close_current(self):
        if self.current_application is not None:
            self.emit("close-requested", self.current_application.window)

    def select_current(self):
        self.select(self.current_application)

    def select(self, application):
        if application is None:
            return

        if self.current_application is not None:
            self.current_application.deselect()

        self.current_application = application
        self.current_application.select()
        self.scroll_to(self.current_application)
        self.emit("selection-changed", self.current_application.window)

    def select_next(self):
        next = self.current_application.get_next_sibling()
        if next is None:
            next = self.application_views.get_first_child()

        self.select(next)

    def select_prev(self):
        prev = self.current_application.get_prev_sibling()
        if prev is None:
            prev = self.application_views.get_last_child()

        self.select(prev)

    def remove_by_window_id(self, window_id):
        if any((current := av).window.id == window_id for av in self):
            self.remove_application(current)
            return True

        return False

    def remove_application(self, application):
        before = self.application_views.measure(Gtk.Orientation.HORIZONTAL, -1)
        if application == self.current_application:
            self.select_prev()

        self.application_views.remove(application)
        after = self.application_views.measure(Gtk.Orientation.HORIZONTAL, -1)
        self.size_transition(
            self,
            max(self.min_width, min(self.max_width, before.natural)),
            max(self.min_width, min(self.max_width, after.natural)),
        )

    def do_measure(self, orientation, for_size):
        measure = self.application_views.measure(orientation, -1)
        min_size = measure.minimum
        nat_size = measure.natural
        if orientation == Gtk.Orientation.HORIZONTAL:
            if self.max_width is None:
                min_size = min_size
                nat_size = nat_size
            else:
                min_size = min(self.max_width, min_size)
                nat_size = min(self.max_width, nat_size)
            if self.size_transition.current_size is not None:
                nat_size = self.size_transition.current_size

        return (min_size, nat_size, -1, -1)

    def __iter__(self):
        current = self.application_views.get_first_child()
        while current is not None:
            yield current
            current = current.get_next_sibling()


class WorkspaceIndicatorChild(Gtk.Box):
    """
    A GTK Box widget that visually represents a workspace indicator.

    This view is used to display an indicator for a workspace, allowing for
    customization of its width and visual appearance via CSS classes.

    Attributes:
        workspace: The workspace object associated with this indicator.

    Args:
        workspace: The workspace to represent.
        width (int, optional): The width of the indicator. Defaults to 5.
    """

    __gsignals__ = {
        "pressed": (GObject.SignalFlags.RUN_FIRST, None, (Workspace,)),
    }

    def __init__(self, workspace, width=5):
        super().__init__()
        self.workspace = workspace
        self.set_size_request(width, -1)
        self.add_css_class("workspace-indicator")
        self.set_vexpand(True)
        gesture = Gtk.GestureClick.new()
        gesture.set_button(0)
        gesture.connect("pressed", self.on_pressed)
        self.add_controller(gesture)

    def on_pressed(self, gesture, n_press, x, y):
        self.emit("pressed", self.workspace)

    def select(self):
        self.add_css_class("selected")

    def deselect(self):
        self.remove_css_class("selected")


class WorkspaceIndicator(Gtk.Box):
    __gsignals__ = {
        "selection-changed": (GObject.SignalFlags.RUN_FIRST, None, (Workspace, bool))
    }

    def __init__(self, width=5):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.width = width
        self.set_halign(Gtk.Align.START)
        self.set_vexpand(True)
        self.set_name("workspace-indicators")
        self.current = None

    def append_workspace(self, workspace: Workspace):
        workspace_indicator = WorkspaceIndicatorChild(workspace, self.width)
        workspace_indicator.connect("pressed", self.on_pressed)
        self.append(workspace_indicator)

    def on_pressed(self, widget, workspace):
        self.select_by_workspace_id(workspace.id)
        self.emit("selection-changed", workspace, False)

    def select_by_workspace_id(self, workspace_id, animate=True):
        for current in self:
            if current.workspace.id == workspace_id:
                self.select(current, animate=animate)
                break

    def select(self, indicator, animate=True):
        if indicator is None or indicator is self.current:
            return

        if self.current is not None:
            self.current.deselect()

        self.current = indicator
        self.current.select()
        self.emit("selection-changed", self.current.workspace, animate)

    def select_next(self, animate=True):
        next = self.current.get_next_sibling()
        if next is None:
            next = self.get_first_child()

        self.select(next, animate=animate)

    def select_prev(self, animate=True):
        prev = self.current.get_prev_sibling()
        if prev is None:
            prev = self.get_last_child()

        self.select(prev, animate=animate)

    def __iter__(self):
        current = self.get_first_child()
        while current is not None:
            yield current
            current = current.get_next_sibling()


class WorkspaceStack(Gtk.Stack):
    def __init__(self, max_width=None, min_width=None):
        super().__init__()
        self.set_name("workspaces")
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
        self.set_hhomogeneous(False)
        self.set_interpolate_size(True)
        self.max_width = max_width
        self.min_width = min_width
        self.connect("notify::visible-child", self._on_visible_child)
        self.indicator: WorkspaceIndicator = None

    def set_width(self, min_width, max_width):
        self.min_width = min_width
        self.max_width = max_width
        self.get_visible_child().set_width(self.min_width, self.max_width)

    def set_indicator(self, indicator):
        for indicator_child in list(indicator):
            indicator.remove(indicator_child)
        for workspace_view in list(self):
            indicator.append_workspace(workspace_view.workspace)

        self.indicator = indicator
        self.indicator.connect("selection-changed", self.on_selection_changed)

    def add_workspace(self, workspace_view):
        if self.indicator:
            self.indicator.append_workspace(workspace_view.workspace)
        self.add_named(workspace_view, workspace_view.workspace.identifier)

    def _on_visible_child(self, widget, prop):
        self.get_visible_child().set_width(self.min_width, self.max_width)

    def on_selection_changed(self, widget, workspace, animate):
        workspace_view = self.get_child_by_name(workspace.identifier)
        if workspace_view is not None:
            if animate:
                self.set_visible_child(workspace_view)
            else:
                self.set_visible_child_full(
                    workspace.identifier, Gtk.StackTransitionType.NONE
                )
            workspace_view.select_current()
