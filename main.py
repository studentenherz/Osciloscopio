from PyQt5 import QtWidgets, uic, QtGui
from plot import Plot, Channel
from audio import InputStream, OutputStream
import pyaudio
import pyqtgraph as pg
import time

class MainWindow(QtWidgets.QMainWindow):
	'''Main window of the application'''
	
	def __init__(self, ui_file):
		###########################
		# Initialize parent class
		###########################
		super(MainWindow, self).__init__()
		self.setFixedSize(1280, 720)

		###########################
		# Load UI
		###########################
		uic.loadUi(ui_file, self)

		##################################
		# Load and configure time plot
		##################################
		self.time_plot = self.findChild(Plot, 'timeGraph')
		self.time_plot.set_position_label(self.findChild(QtWidgets.QLabel, 'label'), '%.3f ms')
		self.time_plot.setYRange(-1, 1)
		self.time_plot.setLabel('bottom', '<span class="plot-label"> tiempo (ms) <span>')
		self.time_plot.setLabel('left', '<span class="plot-label">amplitud<span>')
		self.time_plot.setMouseEnabled(False, True)
		self.time_plot.showGrid(x=True, y=True)

		#####################################
		# Load and configure frequency plot
		#####################################
		self.freq_plot = self.findChild(Plot, 'freqGraph')
		self.freq_plot.set_position_label(self.findChild(QtWidgets.QLabel, 'label_2'), '%.1f Hz')
		self.freq_plot.setYRange(0, 1)
		self.freq_plot.setLabel('bottom', '<span class="plot-label">frecuencia (Hz)<span>')
		self.freq_plot.setLabel('left', '<span class="plot-label">amplitud<span>')
		self.freq_plot.setMouseEnabled(False, True)
		self.freq_plot.showGrid(x=True, y=True)	

		#############################
		# PyAudio class instance
		#############################
		self.p = pyaudio.PyAudio()

		#############################
		# Streams Parameters
		#############################
		self.chunk = 1024
		self.rate = 44100
		self.format = pyaudio.paInt16
		self.out_freq = 440
		self.wave_form = 'sin'
		
		#############################
		# Streams
		#############################
		self.create_input_stream()
		self.create_output_stream()

		###############################
		# Create channel for streams
		##############################
		self.ch2 = Channel(self.time_plot, self.freq_plot, self.out_stream, '#3dc6e4')
		self.ch1 = Channel(self.time_plot, self.freq_plot, self.in_stream, '#f4e923')

		##############################
		# Play button & bindings
		##############################
		self.play_button = self.findChild(QtWidgets.QPushButton, 'play_sound')
		def _togle_play():
			# print('clicked', self.play_button.isChecked())
			_play_icon = QtGui.QIcon(QtGui.QPixmap('play1.png'))
			_stop_icon = QtGui.QIcon(QtGui.QPixmap('stop.png'))
			_style = 'QPushButton {background-color: %s; color: white; border-radius: 14px; font-size: 14px}'
			if self.play_button.isChecked():
				self.out_stream.play()
				self.play_button.setIcon(_stop_icon)
				# self.play_button.setText('stop')
				self.play_button.setStyleSheet(_style % '#eb2828')
			else:
				self.out_stream.stop()
				self.ch2.erase()
				self.play_button.setIcon(_play_icon)
				# self.play_button.setText('play')
				self.play_button.setStyleSheet(_style % '#3ec91e')
		self.play_button.clicked.connect(_togle_play)
		self.play_button.clicked.emit()

		##############################
		# Frequency selector & bingings
		##############################
		self.freq_input = self.findChild(QtWidgets.QLineEdit, 'freq')
		def _set_frequency():
			self.out_freq = int(self.freq_input.text())
			self.out_stream.set(freq=self.out_freq, wave_form=self.wave_form)
		int_validator = QtGui.QIntValidator()
		self.freq_input.setValidator(int_validator)
		self.freq_input.editingFinished.connect(_set_frequency)

		################################
		# Wave Forms Selectors
		################################
		self.sin_wave_selector = self.findChild(QtWidgets.QPushButton, 'sin')
		self.square_wave_selector = self.findChild(QtWidgets.QPushButton, 'square')
		self.triangular_wave_selector = self.findChild(QtWidgets.QPushButton, 'triangular')
		self.sawtooth_wave_selector = self.findChild(QtWidgets.QPushButton, 'sawtooth')


		def _uncheck():
			self.sin_wave_selector.setChecked(False)
			self.square_wave_selector.setChecked(False)
			self.triangular_wave_selector.setChecked(False)
			self.sawtooth_wave_selector.setChecked(False)
		# sine wave bindings
		def _select_sin():
			_uncheck()
			self.sin_wave_selector.setChecked(True)
			self.wave_form = 'sin'
			self.out_stream.set(freq = self.out_freq, wave_form = self.wave_form)
		self.sin_wave_selector.clicked.connect(_select_sin)
		# square wave bindings
		def _select_square():
			_uncheck()
			self.square_wave_selector.setChecked(True)
			self.wave_form = 'square'
			self.out_stream.set(freq = self.out_freq, wave_form = self.wave_form)
		self.square_wave_selector.clicked.connect(_select_square)
		# triangular wave bindings
		def _select_triangular():
			_uncheck()
			self.triangular_wave_selector.setChecked(True)
			self.wave_form = 'triangular'
			self.out_stream.set(freq = self.out_freq, wave_form = self.wave_form)
		self.triangular_wave_selector.clicked.connect(_select_triangular)
		# sawtooth wave bindings
		def _select_sawtooth():
			_uncheck()
			self.sawtooth_wave_selector.setChecked(True)
			self.wave_form = 'sawtooth'
			self.out_stream.set(freq = self.out_freq, wave_form = self.wave_form)
		self.sawtooth_wave_selector.clicked.connect(_select_sawtooth)
		
		self.sin_wave_selector.setChecked(True)  # selecting sine wave by default
		self.out_stream.set(self.out_freq, 'sin')

		#####################################
		# Gain & bingind
		#####################################
		self.out_gain_selector = self.findChild(QtWidgets.QDial, 'gen_dial')
		def _set_out_gain(x):
			_gain = (x - self.out_gain_selector.minimum()) / (self.out_gain_selector.maximum() - self.out_gain_selector.minimum())
			self.out_stream.set_gain(_gain)
		self.out_gain_selector.valueChanged.connect(_set_out_gain)
		self.out_gain_selector.setInvertedControls(True)
		self.out_gain_selector.setSliderPosition((self.out_gain_selector.maximum() + self.out_gain_selector.minimum())//2)

		##################################
		# Chunk size selector & binding
		##################################
		self.chunk_selector = self.findChild(QtWidgets.QComboBox, 'chunk')
		self.chunk_selector.addItems(['256', '512', '1024', '2048'])
		def _change_chunk(chunk_idx):
			_chunk_size = {
				0: 256,
				1: 512,
				2: 1024,
				3: 2048
			}
			self.chunk = _chunk_size[chunk_idx]
			self.close_input_stream()
			self.create_input_stream(chunk=self.chunk, rate = self.rate, format = self.format)
			self.ch1.update_stream(self.in_stream)
		self.chunk_selector.currentIndexChanged.connect(_change_chunk)
		self.chunk_selector.setCurrentIndex(2)

		##################################
		# Bitrate selector & binding
		##################################
		self.rate_selector = self.findChild(QtWidgets.QComboBox, 'rate')
		self.rate_selector.addItems(['16000', '44100', '48000'])
		def _change_rate(rate_idx):
			_rate = {
				0: 16000,
				1: 44100,
				2: 48000
			}
			self.rate = _rate[rate_idx]
			self.close_input_stream()
			self.create_input_stream(rate=self.rate, chunk=self.chunk, format=self.format)
			self.ch1.update_stream(self.in_stream)
		self.rate_selector.currentIndexChanged.connect(_change_rate)
		self.rate_selector.setCurrentIndex(1)

		##################################
		# Depth selector & binding
		##################################
		self.format_selector = self.findChild(QtWidgets.QComboBox, 'depth')
		self.format_selector.addItems(['8 bits', '16 bits', '24 bits', '32 bits'])
		def _change_format(format_idx):
			_format = {
				0: pyaudio.paInt8,
				1: pyaudio.paInt16,
				2: pyaudio.paInt24,
				3: pyaudio.paInt32
			}
			self.format = _format[format_idx]
			self.close_input_stream()
			self.create_input_stream(rate=self.rate, chunk=self.chunk, format=self.format)
			self.ch1.update_stream(self.in_stream)
		self.format_selector.currentIndexChanged.connect(_change_format)
		self.format_selector.setCurrentIndex(1)

		#########################################################
		# Checkbox for logarothmic scale on the frequency plot
		#########################################################
		self.log_checkbox = self.findChild(QtWidgets.QCheckBox, 'log')
		def _toggle_fft_log():
			self.freq_plot.set_log_mode(self.log_checkbox.isChecked(), False)
			self.freq_plot.setYRange(0, 1)
		self.log_checkbox.stateChanged.connect(_toggle_fft_log)
		self.log_checkbox.setChecked(True)


	# Input Stream
	def create_input_stream(self, chunk=1024, rate=44100, format=pyaudio.paInt16, channels=1):
		self.in_stream = InputStream(self.p, chunk, rate, format, channels)
		self.in_stream.start_stream()

	def close_input_stream(self):
		self.in_stream.stop_stream()

	# Output Stream
	def create_output_stream(self, chunk=1024, rate=44100, format=pyaudio.paInt16, channels=1):
		self.out_stream = OutputStream(self.p, chunk, rate, format, channels)
	
	def terminate_pyaudio(self):
		self.p.terminate()


#######################
# QtApplication
#######################
app = QtWidgets.QApplication([])

#######################
# Main Window 
#######################
main = MainWindow('mainwindow.ui')

# Display de widget 
main.show() 

# Start the Qt event loop
app.exec_()

# Close streas & terminate PyAudio
main.close_input_stream()
main.terminate_pyaudio()

