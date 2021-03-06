import gtk
import gobject
import os
import glob
from palette import Palette


class PaletteList(gtk.ListStore):
  """
  A list of available palettes for use with a combo box
  """
  def __init__(self):
    """ Initialize palette list"""
    super(PaletteList,self).__init__(gobject.TYPE_STRING, gobject.TYPE_STRING, Palette, gtk.gdk.Pixbuf)

  def generate_pixbuf(self, palette):
    """Generate an icon representation of a palette"""
    num = len(palette.colors)
    if num == 0:
      return None
    w = 32
    if num < 8:
      sw = 32
      sh = 32 / num
      h = sh * num
    elif num < 16:
      sw = 16
      sh = 32 / (num / 2)
      h = sh * num / 2
    elif num < 32:
      sw = 4
      sh = 32 / (num / 4)
      h = sh * num / 4
    elif num < 64:
      sw = 4
      sh = 32 / (num / 8)
      h = sh * num / 8
    else:
      sw = 4
      sh = 4
      h = 32

    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 0, 8, w, h)
    pixels = pb.get_pixels_array()

    for x in range(0,w):
      for y in range(0,h):
        #border
        if x == 0 or y == 0 or x == w-1 or y == h -1:
          pixels[y,x] = (64,64,64)
          continue

        i = (w / sw) * (y/sh) + (x/sw)
        if i < num:
          pixels[y,x] = palette.colors[i].rgb()
        else:
          pixels[y,x] = (255,255,255)

    return pb

  def load(self, dir):
    """ Load all palettes in a directory """
    for f in glob.glob(os.path.join(dir,'*.gpl')):
      self.append_path(f)

  def append(self, palette):
    """ Add a palette to the end of the list """
    palette.connect('changed', self.palette_changed)
    super(PaletteList,self).append((palette.name, palette.filename, palette, self.generate_pixbuf(palette)))

  def append_path(self, path):
    """ Add a palette to the end of the list by specifying its path """
    p = Palette()
    if p.load(path):
      self.append(p)

  def set_text(self, index, text):
    """
    Set the name of a palette

    This is called when an editable combo box is edited
    """
    row = self[index]
    row[0] = row[2].name = text

  def index_of_palette(self, palette):
    """
    The index of a given palette
    """

    index = 0
    for row in self:
      if row[2] == palette:
        return index
      index += 1
    return None

  def index_of_file(self, file):
    """
    The index of the palette with the given filename
    """
    index = 0
    for row in self:
      if row[1] and os.path.basename(row[1]) == os.path.basename(file):
        return index
      index += 1
    return None

  def palette_changed(self, palette):
    """
    Callback called when a palette is changed

    This regenerates the icon
    """
    index = self.index_of_palette(palette)
    if index != None:
      self[index][3] = self.generate_pixbuf(palette)


class PaletteCombo(gtk.ComboBoxEntry):
  """
  An combo box that displays the available palettes

  The name of the currently selected palette is also editable
  """
  __gsignals__ = {
    'selected': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (Palette,))
    }
  def __init__(self):
    """Initialize empty combo box"""
    super(PaletteCombo,self).__init__()

    self.set_text_column(0)
    self.active = -1

    cell = gtk.CellRendererPixbuf()
    self.pack_start(cell, False)
    self.add_attribute(cell, 'pixbuf', 3)

    self.connect('changed', self.changed)

  def remove(self, index):
    """
    Remove the palette at the specified index

    After removing the palette from the list, the topmost palette is
    selected
    """
    # XXX this is a bit hackish. but, prevents the removed item's name from getting attached to a different item when the changed cb is called. need to find a better way to do this.
    if index == self.active:
      self.active = -1
    list = self.get_model()
    iter = list.get_iter(index)
    list.remove(iter)
    if self.active == -1:
      self.select(0)

  def select(self, index):
    """ Select the palette at the specified index """
    self.set_active(index)
    if self.active != index:
      self.active = index
      self.emit('selected', self.get_model()[index][2])

  def changed(self,combo):
    """ Callback called when the selection is changed or name is edited """
    index = self.get_active()
    if index == -1 and self.active != -1:
      row = self.get_model()[self.active]
      self.get_model().set_text(self.active, combo.child.get_text())
      self.select(self.active)
    else:
      self.select(index)

