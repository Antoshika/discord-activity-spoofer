import tkinter as tk

from modules.theme import M3Blue
from modules.widgets import (
    M3PillInput,
    M3ProgressBar,
    M3StatusPill,
    M3SurfaceCard,
    M3VectorButton,
)


def build_status_bar(main_wrap: tk.Widget, app):
    status_card = M3SurfaceCard(
        main_wrap,
        bg_parent=M3Blue.SURFACE,
        fill_color=M3Blue.SURFACE_CONTAINER_LOW,
        outline_color=M3Blue.OUTLINE,
        radius=14,
        padx=16,
        pady=6,
        expand_v=False,
        fixed_height=34,
    )
    status_card.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    app.status_var = tk.StringVar(value="Initializing Material You 3 environment...")
    tk.Label(
        status_card.inner,
        textvariable=app.status_var,
        bg=M3Blue.SURFACE_CONTAINER_LOW,
        fg=M3Blue.ON_SURFACE_VARIANT,
        anchor="w",
        font=("Segoe UI", 9),
    ).pack(side=tk.LEFT, fill=tk.X, expand=True)


def build_bottom_bar(main_wrap: tk.Widget, app):
    bottom_card = M3SurfaceCard(
        main_wrap,
        bg_parent=M3Blue.SURFACE,
        fill_color=M3Blue.SURFACE_CONTAINER,
        outline_color=M3Blue.OUTLINE,
        radius=22,
        padx=16,
        pady=10,
        expand_v=False,
        fixed_height=62,
    )
    bottom_card.pack(fill=tk.X, side=tk.BOTTOM, pady=(12, 0))

    app.btn_toggle_run = M3VectorButton(
        bottom_card.inner,
        text="Launch Game",
        icon="play",
        variant="filled",
        bg_parent=M3Blue.SURFACE_CONTAINER,
        width=185,
        height=40,
        command=app.toggle_run_stop,
    )
    app.btn_toggle_run.pack(side=tk.LEFT)

    app.btn_autofarm = M3VectorButton(
        bottom_card.inner,
        text="Auto-Farm Selected",
        icon="queue",
        variant="tonal",
        bg_parent=M3Blue.SURFACE_CONTAINER,
        width=210,
        height=40,
        command=app.start_autofarm,
    )
    app.btn_autofarm.pack(side=tk.RIGHT)

    app.interval_input = M3PillInput(
        bottom_card.inner,
        bg_parent=M3Blue.SURFACE_CONTAINER,
        width=86,
        height=38,
        default_val="300",
    )
    app.interval_input.pack(side=tk.RIGHT, padx=(8, 12))

    tk.Label(
        bottom_card.inner,
        text="Interval (sec):",
        bg=M3Blue.SURFACE_CONTAINER,
        fg=M3Blue.ON_SURFACE_VARIANT,
        font=("Segoe UI Semibold", 9),
    ).pack(side=tk.RIGHT)


def build_hero_card(main_wrap: tk.Widget, app):
    header = tk.Frame(main_wrap, bg=M3Blue.SURFACE)
    header.pack(fill=tk.X, pady=(0, 10))

    app.priority_pill = M3StatusPill(
        header,
        text="GLOBAL PRIORITY: STANDBY",
        bg_parent=M3Blue.SURFACE,
        fill_color=M3Blue.SURFACE_CONTAINER,
        fg_color=M3Blue.ON_SURFACE_VARIANT,
        width=265,
        height=34,
    )
    app.priority_pill.pack(side=tk.RIGHT)

    hero_card = M3SurfaceCard(
        main_wrap,
        bg_parent=M3Blue.SURFACE,
        fill_color=M3Blue.PRIMARY_CONTAINER,
        outline_color=M3Blue.PRIMARY,
        radius=24,
        padx=20,
        pady=12,
        expand_v=False,
        fixed_height=116,
    )
    hero_card.pack(fill=tk.X, pady=(0, 12))

    hero_row = tk.Frame(hero_card.inner, bg=M3Blue.PRIMARY_CONTAINER)
    hero_row.pack(fill=tk.X)

    hero_info = tk.Frame(hero_row, bg=M3Blue.PRIMARY_CONTAINER)
    hero_info.pack(side=tk.LEFT)

    tk.Label(
        hero_info,
        text="ACTIVE DISCORD SESSION",
        bg=M3Blue.PRIMARY_CONTAINER,
        fg=M3Blue.PRIMARY,
        font=("Segoe UI Semibold", 8),
    ).pack(anchor="w")

    app.active_game_lbl = tk.Label(
        hero_info,
        text="Waiting for game launch...",
        bg=M3Blue.PRIMARY_CONTAINER,
        fg=M3Blue.ON_PRIMARY_CONTAINER,
        font=("Segoe UI Semibold", 13),
    )
    app.active_game_lbl.pack(anchor="w", pady=(2, 0))

    app.timer_lbl = tk.Label(
        hero_row,
        text="00:00:00",
        bg=M3Blue.PRIMARY_CONTAINER,
        fg=M3Blue.ON_PRIMARY_CONTAINER,
        font=("Consolas", 16, "bold"),
    )
    app.timer_lbl.pack(side=tk.RIGHT)

    app.queue_info_lbl = tk.Label(
        hero_card.inner,
        text="Queue: Idle",
        bg=M3Blue.PRIMARY_CONTAINER,
        fg=M3Blue.ON_PRIMARY_CONTAINER,
        anchor="w",
        font=("Segoe UI", 9),
    )
    app.queue_info_lbl.pack(fill=tk.X, pady=(4, 2))

    app.progress_bar = M3ProgressBar(
        hero_card.inner,
        bg_parent=M3Blue.PRIMARY_CONTAINER,
        track_color=M3Blue.SURFACE_CONTAINER_LOW,
        bar_color=M3Blue.PRIMARY,
        height=7,
    )
    app.progress_bar.pack(fill=tk.X, pady=(4, 0))
