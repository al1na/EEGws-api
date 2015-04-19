"""
https://github.com/fnielsen/brede/blob/draft/brede/eeg/core.py
"""

"""Core data structures for EEG data."""


from __future__ import absolute_import, division, print_function

# Absolute path here because of circular dependency
import brede.io

import matplotlib.pyplot as plt

import numpy as np

from pandas import DataFrame
from pandas import read_csv as pandas_read_csv


ELECTRODES = {
    'AF3',
    'AF4',
    'AF7',
    'AF8',
    'AFz',
    'C1',
    'C2',
    'C3',
    'C4',
    'C5',
    'C6',
    'CP1',
    'CP2',
    'CP3',
    'CP4',
    'CP5',
    'CP6',
    'CPz',
    'Cz',
    'F1',
    'F2',
    'F3',
    'F4',
    'F5',
    'F6',
    'F7',
    'F8',
    'FC1',
    'FC2',
    'FC3',
    'FC4',
    'FC5',
    'FC6',
    'FCz',
    'FP1',
    'FP2',
    'Fpz',
    'FT7',
    'FT8',
    'Fz',
    'Iz',
    'Nz',
    'P1',
    'P2',
    'P3',
    'P4',
    'P5',
    'P6',
    'P7',
    'P8',
    'PO3',
    'PO4',
    'PO7',
    'PO8',
    'POz',
    'Pz',
    'O1',
    'O2',
    'Oz',
    'T7',
    'T8',
    'T9',
    'T10',
    'TP7',
    'TP8',
    'TP9',
    'TP10'
}

EMOTIV_TO_EMOCAP_MAP = {
    'F3': 'P4',
    'FC6': 'Fz',
    'P7': 'TP10',
    'T8': 'C3',
    'F7': 'O1',
    'F8': 'F4',
    'T7': 'P3',
    'P8': 'Cz',
    'AF4': 'Fpz',
    'F4': 'F3',
    'AF3': 'O2',
    'O2': 'C4',
    'O1': 'TP9',
    'FC5': 'Pz',
}


class UnevenSamplingRateError(Exception):

    """Exception for uneven sampling intervals."""

    pass


class ElectrodeNameError(Exception):

    """Exception for wrong electrode name."""

    pass


class EEGRun(DataFrame):

    """Represent a EEG data set.

    The Pandas DataFrame class is reused and extended with, e.g., Fourier
    transformation.

    """

    @property
    def _constructor(self):
        return EEGRun

    def __init__(self, data=None, index=None, columns=None, dtype=None,
                 copy=False, sampling_rate=1.0):
        """Construct dataframe-like object."""
        DataFrame.__init__(self, data=data, index=index, columns=columns,
                           dtype=dtype, copy=copy)
        if sampling_rate is not None:
            self.index = np.arange(0, len(self) * sampling_rate, sampling_rate)

    @property
    def sampling_rate(self):
        """Return sampling rate.

        Raises
        ------
        UnevenSamplingRateError

        """
        intervals = np.diff(self.index.values)
        interval = intervals.mean()
        interval_variation = max(intervals - interval) / interval
        if interval_variation > 10 ** -10:
            raise UnevenSamplingRateError
        return 1 / interval

    @classmethod
    def read_csv(cls, filename, sampling_rate=1.0, *args, **kwargs):
        """Read comma-separated file.

        Parameters
        ----------
        filename : str
            Filename for the csv file

        Returns
        -------
        eeg_run : EEGRun
            EEGRun dataframe with read data.

        """
        return cls(pandas_read_csv(filename, *args, **kwargs),
                   sampling_rate=sampling_rate)

    @classmethod
    def read_edf(cls, filename):
        """Read EDF file.

        Parameters
        ----------
        filename : str
            Filename for EDF file.

        Returns
        -------
        eeg_run : EEGRun
            EEGRun dataframe with read data.

        """
        return cls(brede.io.read_edf(filename))

    def emotiv_to_emocap(self, check_all=True, change_qualities=True,
                         inplace=True):
        """Change column names for Emotiv electrodes to Emocap.

        Specialized method to change the electrode names in the dataframe
        column from Emotiv electrode names to Emocap electrode names.

        """
        emotiv_to_emocap_map = EMOTIV_TO_EMOCAP_MAP

        if check_all:
            for column in emotiv_to_emocap_map:
                if column not in self.columns:
                    message = "Electrode '{}' not in columns".format(column)
                    raise ElectrodeNameError(message)

        columns = []
        for column in self.columns:
            if column in emotiv_to_emocap_map:
                columns.append(emotiv_to_emocap_map[column])
            elif (change_qualities and column.endswith(' quality') and
                  column[:-8] in emotiv_to_emocap_map):
                columns.append(emotiv_to_emocap_map[column[:-8]] + ' quality')
            else:
                columns.append(column)

        if inplace:
            self.columns = columns
        else:
            return EEGRun(self, columns=columns)

    def fft(self):
        """Fourier transform of data.

        Returns
        -------
        spectrum : Spectrum
            Dataframe-like with frequencies in rows and electrodes in columns.

        Examples
        --------
        >>> eeg_run = EEGRun({'Cz': [1, -1, 1, -1]})
        >>> fourier = eeg_run.fft()
        >>> fourier.Cz.real
        array([ 0.,  0.,  4.,  0.])

        """
        fourier = np.fft.fft(self, axis=0)
        frequencies = np.fft.fftfreq(self.shape[0], 1 / self.sampling_rate)
        return Spectrum(fourier, index=frequencies, columns=self.columns)


class EEGAuxRun(EEGRun):

    """Represent a EEG data set with auxilliary data.

    The Pandas DataFrame class is reused and extended with, e.g., Fourier
    transformation.

    Attributes
    ----------
    sampling_rate : float
        Sampling rate in Hertz
    electrodes : list of str
        Names for columns that are electrodes

    """

    @property
    def _constructor(self):
        return EEGAuxRun

    def __init__(self, data=None, index=None, columns=None, dtype=None,
                 copy=False, sampling_rate=1.0, electrodes=None):
        """Construct dataframe-like object."""
        EEGRun.__init__(self, data=data, index=index, columns=columns,
                        dtype=dtype, copy=copy)

        if sampling_rate is not None:
            self.index = np.arange(0, len(self) * sampling_rate, sampling_rate)

        if electrodes is None:
            self.electrodes = [column for column in self.columns
                               if column in ELECTRODES]
        else:
            self.electrodes = electrodes

    def emotiv_to_emocap(self, check_all=True, change_qualities=True,
                         inplace=True):
        """Change column names for Emotiv electrodes to Emocap.

        Specialized method to change the electrode names in the dataframe
        column from Emotiv electrode names to Emocap electrode names.

        """
        old_electrodes = self.electrodes
        super(EEGAuxRun, self).emotiv_to_emocap(
            check_all=check_all,
            change_qualities=change_qualities,
            inplace=inplace)
        self.electrodes = [EMOTIV_TO_EMOCAP_MAP[electrode]
                           for electrode in old_electrodes]

    def fft(self):
        """Fourier transform of data.

        Returns
        -------
        spectrum : Spectrum
            Dataframe-like with frequencies in rows and electrodes in columns.

        Examples
        --------
        >>> eeg_run = EEGRun({'Cz': [1, -1, 1, -1]})
        >>> fourier = eeg_run.fft()
        >>> fourier.Cz.real
        array([ 0.,  0.,  4.,  0.])

        """
        fourier = np.fft.fft(self.ix[:, self.electrodes], axis=0)
        frequencies = np.fft.fftfreq(self.shape[0], 1 / self.sampling_rate)
        return Spectrum(fourier, index=frequencies, columns=self.electrodes)


read_csv = EEGAuxRun.read_csv


class Spectrum(DataFrame):

    """Represent a spectrum for an EEG signal as a dataframe-like object."""

    def plot_electrode_spectrum(self, electrode):
        """Plot the spectrum of an electrode.

        Parameters
        ----------
        electrode : str
            Electrode name associated with column

        """
        positive_frequencies = self.index >= 0
        plt.plot(self.index[positive_frequencies],
                 np.abs(self.ix[positive_frequencies, electrode]))
        plt.xlabel('Frequency')
        plt.ylabel('Magnitude')
        plt.title('Spectrum of {}'.format(electrode))

    def plot_mean_spectrum(self):
        """Plot the spectrum of the mean across electrodes.

        Only the positive part of the spectrum is shown.

        """
        positive_frequencies = self.index >= 0
        plt.plot(self.index[positive_frequencies],
                 np.mean(np.abs(self.ix[positive_frequencies, :]), axis=1))
        plt.xlabel('Frequency')
        plt.ylabel('Magnitude')
        plt.title('Mean spectrum across {} electrodes'.format(self.shape[1]))

    def peak_frequency(self, min_frequency=0.0, max_frequency=None,
                       electrode=None):
        """Return frequency with peak magnitude.

        Parameters
        ----------
        min_frequency : float
            Minimum frequency to search for peak from
        max_frequency : float
            Maximum frequency to search for peak from
        electrode : str, optional
            Electrode to use for finding peak. If None then the mean of the
            magnitude across all electrodes is used.

        Returns
        -------
        freq : float
            Peak frequency

        Examples
        --------
        >>> spectrum = Spectrum({'Cz': [1, 2, 3, 1, 2, 10, 3, 4, 1]})
        >>> spectrum.peak_frequency()
        5

        """
        min_frequency = max(0.0, min_frequency)
        if max_frequency is None:
            max_frequency = max(self.index)

        indices = (self.index >= min_frequency) & (self.index <= max_frequency)
        if electrode is None:
            magnitudes = np.mean(np.abs(self.ix[indices, :]), axis=1)
        else:
            magnitudes = np.abs(self.ix[indices, electrode])

        peak_frequency = magnitudes.argmax()
        return peak_frequency

    def show(self):
        """Show Matplotlib plot."""
        plt.show()
