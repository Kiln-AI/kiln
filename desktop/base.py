from pystray import MenuItem as item
import pystray
from PIL import Image
import os
import tkinter as tk
import webbrowser

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def show_studio():
    print("show fune studio")
    webbrowser.open("https://github.com/scosman/fune")

def quit_app(icon, item):
    print("quiting fune")
    icon.stop()
    root.destroy()

def run_taskbar():  
    # TODO: resolution, dark mode, and other platforms (windows, linux)
    image = Image.open(resource_path("taskbar.png"))
    menu = (item('Open Fune Studio', show_studio), item('Quit', quit_app))
    icon = pystray.Icon("name", image, "title", menu)
    # running detatched since we use tk mainloop to get events from dock icon
    icon.run_detached()

# TK without a window, to get dock events
root = tk.Tk()
root.withdraw()
root.createcommand('tk::mac::ReopenApplication', show_studio)
show_studio()
run_taskbar() 
root.mainloop()
 