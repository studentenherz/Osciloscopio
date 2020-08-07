from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
import struct
import pyaudio
import threading
from scipy.signal import find_peaks

class Process(QObject):
	''' Process class that implements the interperetation and prossesing of the data from stream'''

	struct_types = {
		pyaudio.paInt32: 'l',
		pyaudio.paInt24: 'i',
		pyaudio.paInt16: 'h',
		pyaudio.paInt8: 'b',
		pyaudio.paFloat32: 'd'
	}

	amp = {
		pyaudio.paInt32: 32,
		pyaudio.paInt24: 24,
		pyaudio.paInt16: 16,
		pyaudio.paInt8: 8,
		pyaudio.paFloat32 : 1
	}

	def __init__(self):
		QObject.__init__(self)

	def get_ndarray_data(self, in_data, frame_count, format):
		_format = self.struct_types[format]
		_amp = 2 ** (self.amp[format] - 1)
		
		_raw_data = np.array(struct.unpack(str(frame_count) + _format, in_data))
		
		return _raw_data / _amp

	def fft(self, time_data):
		# size of the chunk (always an even one)
		_size = len(time_data)

		_fft = np.fft.fft(time_data)[1:_size // 2] * (4 / _size)
		
		return  _fft

	def fundamental_freq(self, fft, n = 1):

		size = len(fft) // n
		hps = np.ones(size)

		for i in range(size):
			for j in range(1, n + 1):
				hps[i] *= fft[i * j]
		
		return hps
		


class InputStream(Process):
	'''Input Stream class'''

	sig_new_data = pyqtSignal(np.ndarray, np.ndarray)

	def __init__(self, pyaudio_object, chunk=1024, rate=44100, format=pyaudio.paInt16, channels=1):
		Process.__init__(self)

		self.chunk = chunk
		self.rate = rate
		self.format = format
		self.channels = channels

		self.stream = pyaudio_object.open(
			format=self.format,
			channels=self.channels,
			frames_per_buffer=self.chunk,
			input=True,
			rate=self.rate,
			stream_callback = self.callback
		)

	def get_x_range(self):
		_t = np.arange(0, self.chunk) / self.rate
		_f = np.fft.fftfreq(self.chunk)[1: self.chunk // 2]  * self.rate

		return _t, _f

	def callback(self, in_data, frame_count, time_info, status):
		_time_data = self.get_ndarray_data(in_data, frame_count, self.format)
		_fft = self.fft(_time_data)

		self.sig_new_data.emit(_time_data, _fft)
		# _,_f = self.get_x_range()
		# print(self.fundamental_freq(_fft) * self.rate / self.chunk )

		return (in_data, pyaudio.paContinue)

	def start_stream(self):
		self.stream.start_stream()

	def stop_stream(self):
		self.stream.stop_stream()

class OutputStream(Process):
	'''Output stream class'''

	sig_new_data = pyqtSignal(np.ndarray, np.ndarray)


	def __init__(self, pyaudio_object, chunk=1024, rate=44100, format=pyaudio.paFloat32, channels=1):
		Process.__init__(self)

		self.chunk = chunk
		self.rate = rate
		self.format = format
		self.channels = channels
		self.gain = 0.5

		self.stream = pyaudio_object.open(
			format=self.format,
			channels=self.channels,
			frames_per_buffer=self.chunk,
			output=True,
			rate=self.rate
		)

		self.data = np.zeros(self.chunk)
		self.playing_state = True

	def get_x_range(self):
		_t = np.arange(0, self.chunk) / self.rate
		_f = np.fft.fftfreq(self.chunk)[1: self.chunk // 2]  * self.rate
		
		return _t, _f

	def triangular_wave(self, freq, t):
		''' Triangular wave function with amplitide 1 '''
		
		def _triang(freq, t):
			# y = A + B * t
			tau = 0.25 / freq  # a quarter of period
			A = [0, 1, 0, -1] 
			B = np.array([1, -1, -1, 1]) / tau
			n = int(t / tau)
			dt = t - n * tau
			return A[n % 4] + B[n % 4] * dt

		_vec_triang = np.vectorize(_triang)
		return _vec_triang(freq, t)

	def sawtooth_wave(self, freq, t, slope=1):
		''' Sawtooth wave function from -1 to 1 '''

		def _sawtooth(freq, t):
			tau = 1.0 / freq
			dt = t - int(t / tau) * tau
			return slope * ( + 2 * dt / tau - 1)
			
		_vec_sawtooth = np.vectorize(_sawtooth)
		return _vec_sawtooth(freq, t)

	def square_wave(self, freq, t):
		''' Square wave function with amplitude 1 '''

		def _square(freq, t):
			tau = 0.5 / freq  # half a period
			n = int(t / tau)
			if n % 2 == 1:
				return 1
			else:
				return 0
			
		_vec_square = np.vectorize(_square)
		return _vec_square(freq, t)

	def sin_wave(self, freq, t):
		return np.sin(2 * freq * np.pi * t)

	def set_gain(self, gain):
		self.gain = gain

	def set(self, freq=440, wave_form='sin'):
		wave_function = {
			'sin': self.sin_wave,
			'triangular': self.triangular_wave,
			'square': self.square_wave,
			'sawtooth': self.sawtooth_wave
		}
		_duration = 0.2
		_t = np.arange(0, _duration, 1/self.rate)
		self.data = 2 ** ( self.amp[self.format] - 1) * wave_function[wave_form](freq, _t)

	def play(self):
		def _play():
			while self.playing_state:
				_t, _f = self.get_x_range()
				_data = self.data * self.gain
				_fft = self.fft(_data[:len(_t)] / ( 2 ** ( self.amp[self.format] - 1)))
				
				self.sig_new_data.emit(_data[:len(_t)] / ( 2 ** ( self.amp[self.format] - 1)), _fft )
				self.stream.write(_data.astype(int))
		
		play_th = threading.Thread(target=_play, args=())
		self.playing_state = True
		play_th.start()

	def stop(self):
		self.playing_state = False