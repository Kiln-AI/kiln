import pystray
from PIL import Image
import os
import tkinter as tk
import webbrowser
import uvicorn
import server.server as server
import sys
import threading
import platform


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, relative_path)


def run_studio():
    uvicorn.run(server.app, host="127.0.0.1", port=8757, log_level="warning")


def run_studio_thread():
    threading.Thread(target=run_studio, daemon=True).start()


def show_studio():
    webbrowser.open("http://localhost:8757")


def quit_app():
    # TODO: this is broken
    root.destroy()
    icon.stop()


def run_taskbar(detached=True):
    # TODO: resolution
    image = Image.open(resource_path("taskbar.png"))
    menu = (
        pystray.MenuItem("Open Fune Studio", show_studio),
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon("name", image, "title", menu)
    if detached:
        # running detached since we use tk mainloop to get events from dock icon
        icon.run_detached()
    else:
        icon.run()


def close_splash():
    try:
        import pyi_splash  # type: ignore

        pyi_splash.close()
    except ModuleNotFoundError:
        pass


def run_windows():
    run_studio_thread()
    show_studio()
    close_splash()
    run_taskbar(detached=False)


# Extra work to get the dock icon to work on macOS
def run_macos():
    # TK without a window, to get dock events
    root = tk.Tk()
    root.withdraw()  # hide the window
    # Register callback for the dock icon to reopen the web app
    root.createcommand("tk::mac::ReopenApplication", show_studio)
    run_taskbar(detached=True)
    # start the server in a thread, show the web app, and start the taskbar
    root.after(10, run_studio_thread)
    root.after(1000, show_studio)
    root.after(1000, close_splash)
    root.mainloop()


if __name__ == "__main__":
    if platform.system() == "Windows":
        run_windows()
    else:
        run_macos()
