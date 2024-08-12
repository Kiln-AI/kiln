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
        self.stopped = False
        thread = threading.Thread(target=self.run_safe, daemon=True)
        thread.start()
        try:
            while not self.started and not self.stopped:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()
            on_quit()

    def run_safe(self):
        try:
            self.run()
        finally:
            self.stopped = True

    def running(self):
        return self.started and not self.stopped


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
    # TODO: Windows not working
    global tray
    if tray:
        tray.stop()
    global root
    if root:
        root.destroy()

    sys.exit(0)


def on_quit():
    global root
    # use main runloop if possible
    if root:
        root.after(100, quit_app)
    else:
        quit_app()


def run_taskbar():
    # TODO: resolution
    image = Image.open(resource_path("taskbar.png"))
    menu = (
        pystray.MenuItem("Open Fune Studio", show_studio),
        pystray.MenuItem("Quit", on_quit),
    )
    global tray
    tray = pystray.Icon("fune", image, "fune", menu)
    # running detached since we use tk mainloop to get events from dock icon
    tray.run_detached()
    return tray


def close_splash():
    try:
        import pyi_splash  # type: ignore

        pyi_splash.close()
    except ModuleNotFoundError:
        pass


if __name__ == "__main__":
    root = None
    tray = None

    # run the server in a thread, and shut down server when main thread exits
    # use_colors=False to disable colored logs, as windows doesn't support them
    config = uvicorn.Config(
        server.app, host="127.0.0.1", port=8757, log_level="warning", use_colors=False
    )
    uni_server = ThreadedServer(config=config)
    with uni_server.run_in_thread():
        if not uni_server.running():
            # Can't start. Likely a port is already in use. Show the web app instead and exit
            show_studio()
            on_quit()
        # TK without a window, to get dock events on MacOS
        root = tk.Tk()
        root.title("fune")
        root.withdraw()  # remove the window
        # Register callback for the dock icon to reopen the web app
        root.createcommand("tk::mac::ReopenApplication", show_studio)
        tray = run_taskbar()
        root.after(10, show_studio)
        root.after(10, close_splash)
        root.mainloop()
