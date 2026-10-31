import tkinter as tk
from collections.abc import Callable

from modules.renderer import SmoothRenderer
from modules.theme import M3Blue


class M3PillInput(tk.Canvas):
    def __init__(self, parent, bg_parent: str, width: int = 90, height: int = 38, default_val: str = "300"):
        super().__init__(parent, bg=bg_parent, width=width, height=height, highlightthickness=0, bd=0)
        self.focused = False
        self._img = None
        self.entry = tk.Entry(
            self,
            bg=M3Blue.SURFACE_HIGH,
            fg=M3Blue.PRIMARY,
            insertbackground=M3Blue.PRIMARY,
            relief=tk.FLAT,
            bd=0,
            justify="center",
            font=("Consolas", 11, "bold"),
        )
        self.entry.insert(0, default_val)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Configure>", self._redraw)

    def _on_focus_in(self, _):
        self.focused = True
        self._redraw()

    def _on_focus_out(self, _):
        self.focused = False
        self._redraw()

    def _redraw(self, _=None):
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        outline = M3Blue.PRIMARY if self.focused else M3Blue.OUTLINE
        self._img = SmoothRenderer.rounded_box(w, h, h // 2, M3Blue.SURFACE_HIGH, outline, 2 if self.focused else 1)
        self.create_image(0, 0, image=self._img, anchor="nw", tags="bg")
        self.entry.place(x=14, y=(h - 20) // 2, width=max(20, w - 28), height=20)

    def get(self) -> str:
        return self.entry.get()


class M3SearchBox(tk.Canvas):
    def __init__(self, parent, textvariable: tk.StringVar, bg_parent: str = M3Blue.SURFACE_CONTAINER, width: int = 260, height: int = 36):
        super().__init__(parent, bg=bg_parent, width=width, height=height, highlightthickness=0, bd=0)
        self.focused = False
        self._img = None
        self.entry = tk.Entry(
            self,
            textvariable=textvariable,
            bg=M3Blue.SURFACE_HIGH,
            fg=M3Blue.ON_SURFACE,
            insertbackground=M3Blue.PRIMARY,
            relief=tk.FLAT,
            bd=0,
            font=("Segoe UI", 10),
        )
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Configure>", self._redraw)

    def _on_focus_in(self, _):
        self.focused = True
        self._redraw()

    def _on_focus_out(self, _):
        self.focused = False
        self._redraw()

    def _redraw(self, _=None):
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        outline = M3Blue.PRIMARY if self.focused else M3Blue.OUTLINE
        self._img = SmoothRenderer.rounded_box(
            w, h, h // 2, M3Blue.SURFACE_HIGH, outline, 2 if self.focused else 1, "search", M3Blue.PRIMARY, 20
        )
        self.create_image(0, 0, image=self._img, anchor="nw", tags="bg")
        self.entry.place(x=36, y=(h - 20) // 2, width=max(30, w - 50), height=20)


class M3SmoothScrollbar(tk.Canvas):
    def __init__(self, parent, command: Callable[..., None] | None = None, bg_color: str = M3Blue.SURFACE_CONTAINER, width: int = 10):
        super().__init__(parent, bg=bg_color, width=width, highlightthickness=0, bd=0)
        self.command = command
        self.first = 0.0
        self.last = 1.0
        self.hovered = False
        self.dragging = False
        self.drag_start_y = 0
        self.drag_start_first = 0.0

        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def set(self, first: float, last: float):
        self.first = float(first)
        self.last = float(last)
        self._redraw()

    def _set_hover(self, state: bool):
        self.hovered = state
        self._redraw()

    def _on_press(self, event):
        h = max(1, self.winfo_height())
        y1 = int(self.first * h)
        y2 = int(self.last * h)
        if y1 <= event.y <= y2:
            self.dragging = True
            self.drag_start_y = event.y
            self.drag_start_first = self.first
        elif self.command:
            target = (event.y / h) - (self.last - self.first) / 2
            self.command("moveto", max(0.0, min(1.0, target)))

    def _on_drag(self, event):
        if self.dragging and self.command:
            h = max(1, self.winfo_height())
            dy = (event.y - self.drag_start_y) / h
            self.command("moveto", max(0.0, min(1.0, self.drag_start_first + dy)))

    def _on_release(self, _):
        self.dragging = False

    def _redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if h < 20 or (self.last - self.first) >= 0.999:
            return
        y1 = int(self.first * h) + 4
        y2 = int(self.last * h) - 4
        thumb_h = max(28, y2 - y1)
        if y1 + thumb_h > h - 4:
            y1 = h - 4 - thumb_h

        color = M3Blue.PRIMARY if (self.hovered or self.dragging) else M3Blue.SURFACE_HIGHEST
        cx = w // 2
        self.create_line(cx, y1 + 3, cx, y1 + thumb_h - 3, fill=color, width=w - 3, capstyle=tk.ROUND)
