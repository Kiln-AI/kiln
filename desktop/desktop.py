import pystray
from PIL import Image
import os
import tkinter as tk
import webbrowser
import uvicorn
import server.server as server
import sys
import threading
import contextlib
import time


class ThreadedServer(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, relative_path)


def run_studio():
    uvicorn.run(server.app, host="127.0.0.1", port=8757, log_level="warning")


def run_studio_thread():
    thread = threading.Thread(target=run_studio)
    thread.start()
    return thread


def show_studio():
    webbrowser.open("http://localhost:8757")


def quit_app():
    root.destroy()


def run_taskbar():
    # TODO: resolution
    image = Image.open(resource_path("taskbar.png"))
    menu = (
        pystray.MenuItem("Open Fune Studio", show_studio),
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon("name", image, "title", menu)
    # running detached since we use tk mainloop to get events from dock icon
    icon.run_detached()


def close_splash():
    try:
        import pyi_splash  # type: ignore

        pyi_splash.close()
    except ModuleNotFoundError:
        pass


if __name__ == "__main__":
    # run the server in a thread, and shut down server when main thread exits
    config = uvicorn.Config(
        server.app, host="127.0.0.1", port=8757, log_level="warning", use_colors=False
    )
    with ThreadedServer(
        config=config,
    ).run_in_thread():
        # TK without a window, to get dock events
        root = tk.Tk()
        root.withdraw()  # hide the window
        # Register callback for the dock icon to reopen the web app
        root.createcommand("tk::mac::ReopenApplication", show_studio)
        run_taskbar()
        root.after(10, show_studio)
        root.after(10, close_splash)
        root.mainloop()
        print("Stopping fune")
