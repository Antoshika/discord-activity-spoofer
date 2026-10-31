import tkinter as tk
from tkinter import ttk

from modules.theme import M3Blue
from modules.widgets import (
    M3FilterChip,
    M3SearchBox,
    M3SmoothScrollbar,
    M3SurfaceCard,
)


def build_toolbar(main_wrap: tk.Widget, app):
    toolbar_card = M3SurfaceCard(
        main_wrap,
        bg_parent=M3Blue.SURFACE,
        fill_color=M3Blue.SURFACE_CONTAINER,
        outline_color=M3Blue.OUTLINE,
        radius=20,
        padx=14,
        pady=9,
        expand_v=False,
        fixed_height=54,
    )
    toolbar_card.pack(fill=tk.X, pady=(0, 12))

    app.search_var = tk.StringVar()
    app.search_var.trace_add("write", app._on_search_typed)

    app.search_box = M3SearchBox(
        toolbar_card.inner,
        textvariable=app.search_var,
        bg_parent=M3Blue.SURFACE_CONTAINER,
        width=225,
        height=36,
    )
    app.search_box.pack(side=tk.LEFT, padx=(0, 8))

    app.only_steam_var = tk.BooleanVar(value=False)
    app.chip_steam = M3FilterChip(
        toolbar_card.inner,
        text="My Steam Library",
        variable=app.only_steam_var,
        command=app.update_game_list,
        bg_parent=M3Blue.SURFACE_CONTAINER,
        width=165,
        height=36,
    )
    app.chip_steam.pack(side=tk.LEFT, padx=(0, 8))

    app.ipc_lock_var = tk.BooleanVar(value=True)
    app.chip_priority = M3FilterChip(
        toolbar_card.inner,
        text="Priority Over Everything",
        variable=app.ipc_lock_var,
        bg_parent=M3Blue.SURFACE_CONTAINER,
        width=195,
        height=36,
    )
    app.chip_priority.pack(side=tk.LEFT, padx=(0, 8))

    app.select_all_var = tk.BooleanVar(value=False)
    app.chip_select_all = M3FilterChip(
        toolbar_card.inner,
        text="Select All",
        variable=app.select_all_var,
        command=app._on_select_all_toggled,
        bg_parent=M3Blue.SURFACE_CONTAINER,
        width=118,
        height=36,
    )
    app.chip_select_all.pack(side=tk.LEFT)

    app.count_label = tk.Label(
        toolbar_card.inner,
        text="Games: 0 | Selected: 0",
        bg=M3Blue.SURFACE_CONTAINER,
        fg=M3Blue.PRIMARY,
        font=("Segoe UI Semibold", 9),
    )
    app.count_label.pack(side=tk.RIGHT, padx=(0, 4))


def build_table_panel(main_wrap: tk.Widget, app):
    table_card = M3SurfaceCard(
        main_wrap,
        bg_parent=M3Blue.SURFACE,
        fill_color=M3Blue.SURFACE_CONTAINER,
        outline_color=M3Blue.OUTLINE,
        radius=22,
        padx=14,
        pady=12,
        expand_v=True,
    )
    table_card.pack(fill=tk.BOTH, expand=True)

    header_pill = M3SurfaceCard(
        table_card.inner,
        bg_parent=M3Blue.SURFACE_CONTAINER,
        fill_color=M3Blue.SURFACE_HIGH,
        outline_color=M3Blue.OUTLINE,
        radius=14,
        padx=16,
        pady=8,
        expand_v=False,
        fixed_height=38,
    )
    header_pill.pack(fill=tk.X, side=tk.TOP, pady=(0, 6))

    header_pill.inner.columnconfigure(0, weight=6, uniform="tbl_cols")
    header_pill.inner.columnconfigure(1, weight=4, uniform="tbl_cols")

    tk.Label(
        header_pill.inner,
        text="GAME TITLE",
        bg=M3Blue.SURFACE_HIGH,
        fg=M3Blue.PRIMARY,
        anchor="w",
        font=("Segoe UI Semibold", 9),
    ).grid(row=0, column=0, sticky="we")

    tk.Label(
        header_pill.inner,
        text="EXECUTABLE PROCESS",
        bg=M3Blue.SURFACE_HIGH,
        fg=M3Blue.PRIMARY,
        anchor="w",
        font=("Segoe UI Semibold", 9),
    ).grid(row=0, column=1, sticky="we", padx=(8, 0))

    tree_body = tk.Frame(table_card.inner, bg=M3Blue.SURFACE_CONTAINER)
    tree_body.pack(fill=tk.BOTH, expand=True)

    app.scrollbar = M3SmoothScrollbar(tree_body, bg_color=M3Blue.SURFACE_CONTAINER, width=10)
    app.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))

    app.tree = ttk.Treeview(
        tree_body,
        columns=("exe",),
        show="tree",
        selectmode="extended",
        style="M3Blue.Treeview",
        yscrollcommand=app._on_tree_scroll,
    )
    app.scrollbar.command = app.tree.yview

    app.tree.column("#0", width=500, anchor="w", stretch=True)
    app.tree.column("exe", width=340, anchor="w", stretch=True)

    app.tree.tag_configure("odd", background=M3Blue.SURFACE_CONTAINER, foreground=M3Blue.ON_SURFACE)
    app.tree.tag_configure("even", background=M3Blue.SURFACE_ROW_ALT, foreground=M3Blue.ON_SURFACE)

    app.tree.bind("<Configure>", app._sync_tree_columns)
    app.tree.bind("<Double-1>", lambda e: app.run_selected_game())
    app.tree.bind("<ButtonRelease-1>", app._on_tree_click_release)
    app.tree.bind("<<TreeviewSelect>>", app._on_tree_selection_changed)
    app.tree.bind("<Control-a>", app._on_ctrl_a)
    app.tree.bind("<Control-A>", app._on_ctrl_a)

    app.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
