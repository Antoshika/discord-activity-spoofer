import tkinter as tk

from modules.renderer import SmoothRenderer


class GameListController:
    PAGE_SIZE = 80

    def __init__(self, app):
        self.app = app

    def update_counts_display(self):
        total = len(self.app.filtered_games)
        if self.app.select_all_var.get():
            selected = total
        else:
            selected = len(self.app.tree.selection())
        self.app.count_label.config(text=f"Games: {total} | Selected: {selected}")

    def on_select_all_toggled(self):
        children = self.app.tree.get_children()
        if self.app.select_all_var.get():
            if children:
                self.app.tree.selection_set(children)
            self.app.set_status(f"Selected all {len(self.app.filtered_games)} games in the current list.")
        else:
            if children:
                self.app.tree.selection_remove(children)
            self.app.set_status("Selection cleared.")
        self.update_counts_display()

    def on_ctrl_a(self, _=None):
        self.app.select_all_var.set(True)
        self.on_select_all_toggled()
        return "break"

    def on_tree_click_release(self, _=None):
        if self.app.select_all_var.get():
            children = self.app.tree.get_children()
            if len(self.app.tree.selection()) < len(children):
                self.app.select_all_var.set(False)
        self.update_counts_display()

    def on_tree_selection_changed(self, _=None):
        if self.app.select_all_var.get():
            children = self.app.tree.get_children()
            if len(self.app.tree.selection()) < len(children):
                self.app.select_all_var.set(False)
        self.update_counts_display()

    def on_search_typed(self, *_):
        if self.app._search_after_id:
            self.app.root.after_cancel(self.app._search_after_id)
        self.app._search_after_id = self.app.root.after(100, self.update_game_list)

    def sync_tree_columns(self, event):
        w = event.width
        if w > 100:
            col0 = int(w * 0.6)
            col1 = w - col0 - 4
            self.app.tree.column("#0", width=col0)
            self.app.tree.column("exe", width=col1)

    def on_tree_scroll(self, first, last):
        self.app.scrollbar.set(first, last)
        if float(last) > 0.85 and self.app.rendered_count < len(self.app.filtered_games):
            self.append_next_page()
        if self.app._scroll_after_id:
            self.app.root.after_cancel(self.app._scroll_after_id)
        self.app._scroll_after_id = self.app.root.after(45, self.schedule_visible_icons_fetch)

    def schedule_visible_icons_fetch(self):
        children = self.app.tree.get_children()
        if not children:
            return

        top_iid = self.app.tree.identify_row(8)
        bot_iid = self.app.tree.identify_row(max(8, self.app.tree.winfo_height() - 8))
        start_idx = children.index(top_iid) if top_iid in children else 0
        end_idx = children.index(bot_iid) if bot_iid in children else min(len(children) - 1, start_idx + 16)

        visible_slice = children[max(0, start_idx - 2):min(len(children), end_idx + 6)]
        visible_games = [self.app.games_by_id[app_id] for app_id in visible_slice if app_id in self.app.games_by_id]
        self.app.icon_pool.schedule_games(visible_games)

    def update_game_list(self):
        query = self.app.search_var.get().lower().strip()
        only_steam = self.app.only_steam_var.get()

        filtered = [
            g for g in self.app.discord_games
            if (not only_steam or (g["steam_ids"] & self.app.user_steam_appids))
            and (not query or query in g["name_lower"] or query in g["exe_lower"])
        ]

        if query:
            filtered.sort(
                key=lambda g: (
                    0 if g["name_lower"] == query else (1 if g["name_lower"].startswith(query) else 2),
                    g["name_lower"],
                )
            )

        self.app.filtered_games = filtered
        self.app.rendered_count = 0
        self.app.tree.delete(*self.app.tree.get_children())
        self.update_counts_display()

        self.append_next_page()
        self.app.tree.yview_moveto(0.0)
        self.app.root.after(20, self.schedule_visible_icons_fetch)

    def append_next_page(self):
        start_idx = self.app.rendered_count
        end_idx = min(start_idx + self.PAGE_SIZE, len(self.app.filtered_games))
        if start_idx >= end_idx:
            return

        default_icon = SmoothRenderer.get_default_game_icon(size=30)
        newly_inserted = []
        for idx in range(start_idx, end_idx):
            g = self.app.filtered_games[idx]
            app_id = g["id"]
            if self.app.tree.exists(app_id):
                continue
            tag = "even" if idx % 2 == 0 else "odd"
            icon_img = self.app.custom_icons_cache.get(app_id, default_icon)
            self.app.tree.insert(
                "",
                tk.END,
                iid=app_id,
                text=f"  {g['name']}",
                image=icon_img,
                values=(f"  {g['exe']}",),
                tags=(tag,),
            )
            newly_inserted.append(app_id)
        self.app.rendered_count = end_idx
        if self.app.select_all_var.get() and newly_inserted:
            self.app.tree.selection_add(newly_inserted)
        self.update_counts_display()
