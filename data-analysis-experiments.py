#Based on http://gribblelab.org/scicomp/09_Signals_sampling_filtering.html

import numpy
from numpy.random import randn
from numpy import sin
from math import pi
from matplotlib import mlab
from matplotlib import pyplot as plt
from pylab import *

# construct signal
plt.figure(figsize=(6,8))
#t = numpy.linspace(0, 1, 201)  # 200 Hz sampling rate
Fs=200.
F=50.
t = [i*1./Fs for i in range(200)]
y = sin(2*pi*numpy.array(t)*F) + randn(len(t))/2  # 50 Hz signal plus noise

#plot in the time domain
plt.subplot(211)
plt.plot(t, y, 'b-')
plt.xlabel("TIME (sec)")
plt.ylabel("SIGNAL MAGNITUDE")

# compute and plot the power spectral density (PSD)
plt.subplot(212)
# psd = plt.psd(y, Fs=200)
psd = mlab.psd(y, Fs=200)
# y : array_like - Time series of measurement values
# Fs : float, optional - Sampling frequency of the x time series in units of Hz. Defaults to 1.0.
plt.plot(psd[1], psd[0], 'r-')
plt.xlabel("FREQUENCY")
plt.ylabel("POWER SPECTRAL DENSITY")
plt.savefig("mlab_signal_50_psd.jpg", dpi=150)

# compute FFT (Fast Fourier Transform) and plot the magnitude spectrum
fourier = numpy.fft.fft(y)
frequencies = numpy.fft.fftfreq(len(t), 0.005)  # where 0.005 is the inter-sample time difference
positive_frequencies = frequencies[numpy.where(frequencies >= 0)]  # only the positive frequencies
magnitudes = abs(fourier[numpy.where(frequencies >= 0)])  # magnitude spectrum
plt.subplot(311)
plt.plot(positive_frequencies, magnitudes, 'g-')
plt.xticks([10, 20, 30, 40, 50, 60, 70, 80, 90])
plt.ylabel("POWER")
plt.xlabel("FREQUENCY (Hz)")
plt.savefig("signal_magnitude_spectrum.jpg", dpi=150)

# compute the dominating frequency
peak_frequency = numpy.argmax(magnitudes)
print("The dominating frequency is " + str(peak_frequency) + " Hz")

# spectrogram
plt.subplot(411)
specgram(y)
plt.savefig("spectrogram.jpg", dpi=150)


