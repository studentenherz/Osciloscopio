import PyQt5
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import numpy as np


class Plot(PlotWidget):
	''' Plot class with handy methods to display the signal inside the oscilloscope '''

	log_mode_x = False
	log_mode_y = False

	def __init__(self, parent=None):
		super(Plot, self).__init__(parent)

		self.setMouseEnabled(False, False)

		self.scene().sigMouseMoved.connect(self.show_mouse_x_position)

	def set_position_label(self, label, form=None):
		self.label = label
		self.label.hide()
		self.form = form

	def set_log_mode(self, x=False, y=False):
		self.setLogMode(x, y)
		self.log_mode_x = x
		self.log_mode_y = y

	def enterEvent(self, event):
		self.label.show()

	def leaveEvent(self, event):
		self.label.hide()

	def show_mouse_x_position(self, event):
		_x = self.plotItem.vb.mapSceneToView(event).x()

		if self.log_mode_x:
			_x = np.power(10, _x)

		self.label.setText(self.form % _x)

class Channel:
	''' A class for the signal channels of the oscilloscope, to put together the adquisition and processing with the visual display '''

	def __init__(self, time_plot, freq_plot, stream, color):

		# get data from stream
		self.t, self.f = stream.get_x_range()
		
		# create line in each plot
		self.time_line = time_plot.plot(self.t, np.zeros(len(self.t)), pen=pg.mkPen(color))
		self.freq_line = freq_plot.plot(self.f, np.zeros(len(self.f)), pen=pg.mkPen(color))
		
		stream.sig_new_data.connect(self._update)
		self.erase()


	def _update(self, time, freq):
		_f_abs = np.abs(freq)
		# _f_real = np.real(freq)
		# _f_img = np.imag(freq)

		self.time_line.setData(self.t, time)
		self.freq_line.setData(self.f[:len(freq)], _f_abs)

	def update_stream(self, stream):
		self.t, self.f = stream.get_x_range()
		stream.sig_new_data.connect(self._update)

	def erase(self):
		self.time_line.setData([], [])
		self.freq_line.setData([], [])