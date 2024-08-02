from pystray import MenuItem as item
import pystray
from PIL import Image
import tkinter as tk

def show_window():
    print("show window")

def quit_app(icon, item):
    icon.stop()

def run_taskbar():  
    image = Image.open("taskbar.png")
    menu = (item('Quit', quit_app), item('Show', show_window))
    icon = pystray.Icon("name", image, "title", menu)
    icon.run()

if __name__ == '__main__':
   show_window()
   run_taskbar() 
 