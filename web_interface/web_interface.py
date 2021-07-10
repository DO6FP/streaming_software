#!/usr/bin/python3
# this module contanis the gtk3+ graphical user interface,
# which is displayed in the browser on the tablet
#
# read the following resources:
# https://python-gtk-3-tutorial.readthedocs.io/en/latest/
# https://developer.gnome.org/pygtk/stable/
# https://developer.gnome.org/gtk3/stable/gtk-broadway.html
#

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def main_loop():

  # define first window
  class MyWindow(Gtk.Window):
    def __init__(self):
      Gtk.Window.__init__(self, title="Hello World")
      
      self.button = Gtk.Button(label="Click Here")
      self.button.connect("clicked", self.on_button_clicked)
      self.add(self.button)
      self.resize(300, 200)

    def on_button_clicked(self, widget):
      print("Hello World")


  win = MyWindow()
  win.connect("destroy", Gtk.main_quit)
  win.show_all()
  Gtk.main()


if __name__ == "__main__":
  main_loop()
