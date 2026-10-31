import ctypes
import os
import sys
import tkinter as tk


def setup_dpi_awareness():
    if hasattr(ctypes, "windll"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("discord.spoofer.app")
        except (AttributeError, OSError):
            pass
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass


def apply_win32_taskbar_and_dwm(root: tk.Tk):
    if not hasattr(ctypes, "windll"):
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if not hwnd:
            hwnd = root.winfo_id()

        gwl_exstyle = -20
        ws_ex_appwindow = 0x00040000
        ws_ex_toolwindow = 0x00000080

        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, gwl_exstyle)
        ex_style = (ex_style & ~ws_ex_toolwindow) | ws_ex_appwindow
        ctypes.windll.user32.SetWindowLongW(hwnd, gwl_exstyle, ex_style)

        h_mod = ctypes.windll.kernel32.GetModuleHandleW(None)
        h_icon = ctypes.windll.user32.LoadIconW(h_mod, 1)
        if h_icon:
            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, h_icon)
            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, h_icon)

        corner_pref = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(corner_pref), ctypes.sizeof(corner_pref))

        border_col = ctypes.c_int(0x00543D29)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(border_col), ctypes.sizeof(border_col))

        root.withdraw()
        root.deiconify()
    except (AttributeError, OSError):
        pass


class WindowFrameController:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.is_maximized = False
        self.normal_geom = "960x720+120+80"
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def setup_custom_frame(self):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(__file__)))
        icon_path = os.path.join(base_dir, "icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_dir, "assets", "icon.png")
        if os.path.exists(icon_path):
            try:
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
            except (tk.TclError, OSError):
                pass
        self.root.update_idletasks()
        self.root.overrideredirect(True)
        self.root.after(20, lambda: apply_win32_taskbar_and_dwm(self.root))

    def minimize_window(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<Map>", self.on_restore_from_taskbar)

    def on_restore_from_taskbar(self, _=None):
        if self.root.state() == "normal":
            self.root.unbind("<Map>")
            self.root.overrideredirect(True)
            self.root.after(10, lambda: apply_win32_taskbar_and_dwm(self.root))

    def toggle_maximize(self, _=None):
        if not self.is_maximized:
            self.normal_geom = self.root.geometry()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight() - 40
            self.root.geometry(f"{sw}x{sh}+0+0")
            self.is_maximized = True
        else:
            self.root.geometry(self.normal_geom)
            self.is_maximized = False

    def start_drag(self, event):
        if not self.is_maximized:
            self.drag_offset_x = event.x_root - self.root.winfo_x()
            self.drag_offset_y = event.y_root - self.root.winfo_y()

    def do_drag(self, event):
        if not self.is_maximized:
            nx = event.x_root - self.drag_offset_x
            ny = event.y_root - self.drag_offset_y
            self.root.geometry(f"+{nx}+{ny}")

    def resize_right(self, event):
        if not self.is_maximized:
            new_w = max(840, event.x_root - self.root.winfo_x())
            self.root.geometry(f"{new_w}x{self.root.winfo_height()}")

    def resize_bottom(self, event):
        if not self.is_maximized:
            new_h = max(580, event.y_root - self.root.winfo_y())
            self.root.geometry(f"{self.root.winfo_width()}x{new_h}")
