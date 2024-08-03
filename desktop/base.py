from pystray import MenuItem as item
import pystray
from PIL import Image
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def show_window():
    print("show window")

def quit_app(icon, item):
    icon.stop()

def run_taskbar():  
    # TODO: resolution, dark mode, and other platforms (windows, linux)
    image = Image.open(resource_path("taskbar.png"))
    menu = (item('Quit', quit_app), item('Show', show_window))
    icon = pystray.Icon("name", image, "title", menu)
    icon.run()

show_window()
run_taskbar() 
 