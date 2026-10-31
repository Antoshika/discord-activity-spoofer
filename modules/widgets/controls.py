import tkinter as tk
from collections.abc import Callable

from modules.renderer import SmoothRenderer
from modules.theme import M3Blue


class M3VectorButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text: str,
        icon: str | None = None,
        command: Callable[[], None] | None = None,
        variant: str = "filled",
        bg_parent: str = M3Blue.SURFACE_CONTAINER,
        width: int = 190,
        height: int = 40,
    ):
        super().__init__(parent, bg=bg_parent, width=width, height=height, highlightthickness=0, bd=0, cursor="hand2")
        self.text = text
        self.icon = icon
        self.command = command
        self.variant = variant
        self.hovered = False
        self._img = None
        self._apply_colors()
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)

    def configure_state(self, text: str, icon: str, variant: str):
        self.text = text
        self.icon = icon
        self.variant = variant
        self._apply_colors()
        self._redraw()

    def _apply_colors(self):
        match self.variant:
            case "filled":
                self.bg_norm = M3Blue.PRIMARY
                self.bg_hover = M3Blue.PRIMARY_HOVER
                self.fg_col = M3Blue.ON_PRIMARY
            case "tonal":
                self.bg_norm = M3Blue.PRIMARY_CONTAINER
                self.bg_hover = M3Blue.PRIMARY_CONTAINER_HOVER
                self.fg_col = M3Blue.ON_PRIMARY_CONTAINER
            case "secondary":
                self.bg_norm = M3Blue.SECONDARY_CONTAINER
                self.bg_hover = M3Blue.SECONDARY_CONTAINER_HOVER
                self.fg_col = M3Blue.ON_SECONDARY_CONTAINER
            case "error":
                self.bg_norm = M3Blue.ERROR_CONTAINER
                self.bg_hover = M3Blue.ERROR_CONTAINER_HOVER
                self.fg_col = M3Blue.ON_ERROR_CONTAINER
            case _:
                self.bg_norm = M3Blue.SURFACE_HIGH
                self.bg_hover = M3Blue.SURFACE_HIGHEST
                self.fg_col = M3Blue.PRIMARY

    def _on_enter(self, _):
        self.hovered = True
        self._redraw()

    def _on_leave(self, _):
        self.hovered = False
        self._redraw()

    def _on_click(self, _):
        if self.command:
            self.command()

    def _redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        fill = self.bg_hover if self.hovered else self.bg_norm
        self._img = SmoothRenderer.rounded_box(w, h, h // 2, fill, None, 0, self.icon, self.fg_col, 24)
        self.create_image(0, 0, image=self._img, anchor="nw")
        offset = 10 if self.icon else 0
        self.create_text(w // 2 + offset, h // 2, text=self.text, fill=self.fg_col, font=("Segoe UI Semibold", 9))


class M3FilterChip(tk.Canvas):
    def __init__(
        self,
        parent,
        text: str,
        variable: tk.BooleanVar,
        command: Callable[[], None] | None = None,
        bg_parent: str = M3Blue.SURFACE_CONTAINER,
        width: int = 200,
        height: int = 36,
    ):
        super().__init__(parent, bg=bg_parent, width=width, height=height, highlightthickness=0, bd=0, cursor="hand2")
        self.text = text
        self.variable = variable
        self.command = command
        self.hovered = False
        self._img = None
        self.variable.trace_add("write", lambda *_: self._redraw())
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._toggle)

    def _on_enter(self, _):
        self.hovered = True
        self._redraw()

    def _on_leave(self, _):
        self.hovered = False
        self._redraw()

    def _toggle(self, _):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        selected = self.variable.get()
        if selected:
            fill = M3Blue.SECONDARY_CONTAINER_HOVER if self.hovered else M3Blue.SECONDARY_CONTAINER
            outline = M3Blue.PRIMARY
            fg = M3Blue.ON_SECONDARY_CONTAINER
            icon = "check"
        else:
            fill = M3Blue.SURFACE_HIGH if self.hovered else M3Blue.SURFACE_CONTAINER_LOW
            outline = M3Blue.OUTLINE
            fg = M3Blue.ON_SURFACE_VARIANT
            icon = None

        self._img = SmoothRenderer.rounded_box(w, h, h // 2, fill, outline, 1, icon, M3Blue.PRIMARY, 20)
        self.create_image(0, 0, image=self._img, anchor="nw")
        offset = 9 if selected else 0
        self.create_text(w // 2 + offset, h // 2, text=self.text, fill=fg, font=("Segoe UI Semibold", 9))


class M3WindowControlButton(tk.Canvas):
    def __init__(self, parent, kind: str, command: Callable[[], None], bg_parent: str = M3Blue.TITLEBAR):
        super().__init__(parent, bg=bg_parent, width=38, height=28, highlightthickness=0, bd=0, cursor="hand2")
        self.kind = kind
        self.command = command
        self.hovered = False
        self._img = None
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda e: self.command())

    def _set_hover(self, state: bool):
        self.hovered = state
        self._redraw()

    def _redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if self.hovered:
            bg = M3Blue.ERROR_CONTAINER_HOVER if self.kind == "close" else M3Blue.SURFACE_HIGH
            fg = "#FFFFFF"
            self._img = SmoothRenderer.rounded_box(w, h, 8, bg, None, 0)
            self.create_image(0, 0, image=self._img, anchor="nw")
        else:
            fg = M3Blue.ON_SURFACE_VARIANT

        cx, cy = w // 2, h // 2
        match self.kind:
            case "min":
                self.create_line(cx - 5, cy + 1, cx + 5, cy + 1, fill=fg, width=1.6)
            case "max":
                self.create_rectangle(cx - 5, cy - 4, cx + 5, cy + 5, outline=fg, width=1.4)
            case "close":
                self.create_line(cx - 5, cy - 5, cx + 5, cy + 5, fill=fg, width=1.6)
                self.create_line(cx + 5, cy - 5, cx - 5, cy + 5, fill=fg, width=1.6)
