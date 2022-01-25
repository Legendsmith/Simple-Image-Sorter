import tkinter as tk
from tkinter import ttk

class AutoScrollbar(ttk.Scrollbar):
	""" A scrollbar that hides itself if it's not needed. Works only for grid geometry manager """
	def set(self, lo, hi):
		if float(lo) <= 0.0 and float(hi) >= 1.0:
			self.grid_remove()
		else:
			self.grid()
			ttk.Scrollbar.set(self, lo, hi)

	def pack(self, **kw):
		raise tk.TclError('Cannot use pack with the widget ' + self.__class__.__name__)

	def place(self, **kw):
		raise tk.TclError('Cannot use place with the widget ' + self.__class__.__name__)