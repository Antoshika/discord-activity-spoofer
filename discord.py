import tkinter as tk

from modules.app import DiscordSteamSpooferM3BlueApp
from modules.window_frame import setup_dpi_awareness

setup_dpi_awareness()

if __name__ == "__main__":
    root = tk.Tk()
    app = DiscordSteamSpooferM3BlueApp(root)
    root.mainloop()
