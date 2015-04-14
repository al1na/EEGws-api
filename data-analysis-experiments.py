#Based on http://gribblelab.org/scicomp/09_Signals_sampling_filtering.html

import numpy
from numpy.random import randn
from numpy import sin
from math import pi
from matplotlib import mlab
from matplotlib import pyplot as plt

# construct signal
plt.figure(figsize=(6,8))
t = numpy.linspace(0, 1, 201) #200 Hz sampling rate
y = sin(2*pi*t*50) + randn(len(t))/2 #50 Hz signal plus noise

#plot in the time domain
plt.subplot(211)
plt.plot(t, y, 'b-')
plt.xlabel("TIME (sec)")
plt.ylabel("SIGNAL MAGNITUDE")

# compute and plot the power spectral density (PSD)
plt.subplot(212)
psd = mlab.psd(y, Fs=200)
#y : array_like - Time series of measurement values
#Fs : float, optional - Sampling frequency of the x time series in units of Hz. Defaults to 1.0.
plt.plot(psd[1], psd[0], 'b-')
plt.xlabel("FREQUENCY")
plt.ylabel("POWER SPECTRAL DENSITY")
plt.savefig("mlab_signal_50_psd.jpg", dpi=150)
