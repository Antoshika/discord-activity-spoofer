import tkinter as tk
from tkinter import ttk

from modules.theme import M3Blue
from modules.ui_panels import build_bottom_bar, build_hero_card, build_status_bar
from modules.ui_table import build_table_panel, build_toolbar
from modules.widgets import (
    M3AuthorGifBadge,
    M3WindowControlButton,
)


def setup_treeview_styles():
    style = ttk.Style()
    style.theme_use("clam")
    style.layout("M3Blue.Treeview", [("M3Blue.Treeview.treearea", {"sticky": "nswe"})])
    style.configure(
        "M3Blue.Treeview",
        background=M3Blue.SURFACE_CONTAINER,
        foreground=M3Blue.ON_SURFACE,
        fieldbackground=M3Blue.SURFACE_CONTAINER,
        borderwidth=0,
        relief="flat",
        rowheight=42,
        font=("Segoe UI Semibold", 10),
    )
    style.map(
        "M3Blue.Treeview",
        background=[("selected", M3Blue.PRIMARY_CONTAINER)],
        foreground=[("selected", M3Blue.ON_PRIMARY_CONTAINER)],
    )


def build_titlebar(app_shell: tk.Widget, app):
    titlebar = tk.Frame(app_shell, bg=M3Blue.TITLEBAR, height=44, padx=16)
    titlebar.pack(fill=tk.X, side=tk.TOP)
    titlebar.pack_propagate(False)

    title_lbl = tk.Label(
        titlebar,
        text="Discord Activity Spoofer",
        bg=M3Blue.TITLEBAR,
        fg=M3Blue.ON_SURFACE,
        font=("Segoe UI Semibold", 10),
    )
    title_lbl.pack(side=tk.LEFT)

    app.author_badge = M3AuthorGifBadge(
        titlebar,
        cache_dir=app.base_temp_dir,
        bg_parent=M3Blue.TITLEBAR,
        width=112,
        height=28,
    )
    app.author_badge.pack(side=tk.LEFT, padx=(8, 0))

    btn_close = M3WindowControlButton(titlebar, "close", app.on_close, bg_parent=M3Blue.TITLEBAR)
    btn_close.pack(side=tk.RIGHT, padx=(2, 0))

    btn_max = M3WindowControlButton(titlebar, "max", app._toggle_maximize, bg_parent=M3Blue.TITLEBAR)
    btn_max.pack(side=tk.RIGHT, padx=2)

    btn_min = M3WindowControlButton(titlebar, "min", app._minimize_window, bg_parent=M3Blue.TITLEBAR)
    btn_min.pack(side=tk.RIGHT, padx=2)

    for w in (titlebar, title_lbl, app.author_badge):
        w.bind("<ButtonPress-1>", app._start_window_drag)
        w.bind("<B1-Motion>", app._do_window_drag)
        w.bind("<Double-Button-1>", app._toggle_maximize)


def build_app_ui(app):
    outer_border = tk.Frame(app.root, bg=M3Blue.OUTLINE, padx=1, pady=1)
    outer_border.pack(fill=tk.BOTH, expand=True)

    app_shell = tk.Frame(outer_border, bg=M3Blue.SURFACE)
    app_shell.pack(fill=tk.BOTH, expand=True)

    right_edge = tk.Frame(app_shell, bg=M3Blue.SURFACE, width=5, cursor="sb_h_double_arrow")
    right_edge.pack(side=tk.RIGHT, fill=tk.Y)
    right_edge.bind("<B1-Motion>", app._resize_right)

    bottom_edge = tk.Frame(app_shell, bg=M3Blue.SURFACE, height=5, cursor="sb_v_double_arrow")
    bottom_edge.pack(side=tk.BOTTOM, fill=tk.X)
    bottom_edge.bind("<B1-Motion>", app._resize_bottom)

    build_titlebar(app_shell, app)

    main_wrap = tk.Frame(app_shell, bg=M3Blue.SURFACE, padx=20, pady=12)
    main_wrap.pack(fill=tk.BOTH, expand=True)

    build_status_bar(main_wrap, app)
    build_bottom_bar(main_wrap, app)
    build_hero_card(main_wrap, app)
    build_toolbar(main_wrap, app)
    build_table_panel(main_wrap, app)
