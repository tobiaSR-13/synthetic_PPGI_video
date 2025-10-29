import zipfile
import pandas as pd
#import matplotlib.pyplot as plt
import scipy.signal as sig
import numpy as np
#import pyPPG as ppg

TRIALS = ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08", "v09"]

def readPPG(path, trial):
    """
    reads ppg csv data in zip file and resample it to 30 Hz
    :param path: path to zipfile of dataset
    :param trial: trial from chosen subject that should be used
    :return: timestamp, bvp of signal
    """

    subject_number = path.split(".")[0][-4:]

    if trial not in TRIALS:
        raise AttributeError(f"trial {trial} should be part of {TRIALS}")

    with zipfile.ZipFile(path, 'r') as zip_ref:

        with zip_ref.open(f'{subject_number}/{trial}/BVP.csv') as file:

            bvp_content = pd.read_csv(file)

    time = bvp_content['timestamp']
    time = time - time[0]
    time = time.to_numpy()
    bvp = bvp_content['bvp']
    bvp = bvp - np.mean(bvp)

    # resample to 30 values per second

    fs_new = 30
    duration = time[-1]

    new_num_samples = int(duration * fs_new)

    bvp = sig.resample(bvp, new_num_samples)
    time = np.linspace(0,duration,new_num_samples)

    #plt.plot(time, bvp)
    #plt.show()

    return time, bvp

def signFunction(value, index, peaks, neg_peaks):
    """
    function that inverts the sign of a current value if the current index ist part of negative or positive peaks
    :param value: current value
    :param index: current index
    :param peaks: list of positive peak indices
    :param neg_peaks: list of negative peak indices
    :return: new value
    """
    if index in peaks or index in neg_peaks:
        return -1*value
    else:
        return value

def addFunction(value, index, peaks, neg_peaks):
    """
    function that current value increases by 1 if current index is part of the positive or negative peaks
    :param value: current value
    :param index: current index
    :param peaks: list of positive peaks
    :param neg_peaks: list of negative peaks
    :return: new value
    """
    if index in peaks or index in neg_peaks:
        return value + 1
    else:
        return value

def sign(p, n):
    """
    function returns whether first peak is negative (-1) or positive (1)
    :param p: list of positive peak indices
    :param n: list of negative peak indices
    :return: value -1 or 1
    """
    return 1 if p[0] < n[0] else -1

def getClose2N(arr, n):
    """

    :param arr:
    :param n:
    :return:
    """
    for i, a in enumerate(arr):
        if a-n > 0:
            return i-1, i


def getKeyframes(time, bvp, mode='smooth'):
    """
    get animation and magnitude value for every frame
    :param time: time stamps
    :param bvp: bvp/ppg signal
    :param mode: get all peak values (full) or just the maximum and minimum of each pulse cycle
    :return: animation values for each frame
    :return: magnitude value for each frame
    :return: time stamp
    """

    if mode not in ['full', 'smooth']:
        raise AttributeError(f"Mode {mode} is not known. There is only mode 'full' or 'smooth' available")

    # get positive and negative peaks
    if mode == 'smooth':
        peaks, _ = sig.find_peaks(bvp)
        neg_peaks, _ = sig.find_peaks(-1*bvp)

        # delete all positive peaks where there is a higher value within the last and next 5 indices
        pos_del = []
        for i in range(0, peaks.size):
            n_low = max(peaks[i] - 5, 0)
            n_high = min(peaks[i] + 5, bvp.size)
            if np.max(bvp[n_low:n_high]) > bvp[peaks[i]]: pos_del.append(i)
        peaks = np.delete(peaks, np.array(pos_del))

        # delete all negative peaks where there is a lower value within the last and next 5 indices
        neg_del = []
        for i in range(0, neg_peaks.size):
            n_low = max(neg_peaks[i]-5, 0)
            n_high = min(neg_peaks[i]+5, bvp.size)
            if np.min(bvp[n_low:n_high]) < bvp[neg_peaks[i]]: neg_del.append(i)
        neg_peaks = np.delete(neg_peaks, np.array(neg_del))

        # delete if two pos or neg peaks are next to each other
        labeled = [(x, 'pos') for x in peaks] + [(x, 'neg') for x in neg_peaks]
        labeled.sort(key=lambda x: x[0])  # sort by index value

        pos_del, neg_del = [], []
        for i in range(1, len(labeled)):
            if labeled[i][1] == labeled[i - 1][1]:
                if labeled[i][1] == 'pos':
                    m = np.argmin([bvp[labeled[i][0]], bvp[labeled[i - 1][0]]])
                    pos_del.append(np.where(peaks == labeled[i-m][0])[0][0])

                elif labeled[i][1] == 'neg':
                    m = np.argmax([bvp[labeled[i][0]], bvp[labeled[i - 1][0]]])
                    neg_del.append(np.where(neg_peaks == labeled[i-m][0])[0][0])

        # correct if there is a neg peak above 0
        for i, n in enumerate(neg_peaks):
            if bvp[n] > 0:
                i_low, i_up = getClose2N(peaks, n)
                if bvp[peaks[i_low]] > bvp[peaks[i_up]]:
                    pos_del.append(i_up)
                else:
                    pos_del.append(i_low)
                neg_del.append(i)

        # correct if there is a pos peak below 0
        for i, p in enumerate(peaks):
            if bvp[p] < 0:
                i_low, i_up = getClose2N(neg_peaks, p)
                if bvp[neg_peaks[i_low]] < bvp[neg_peaks[i_up]]:
                    neg_del.append(i_up)
                else:
                    neg_del.append(i_low)
                pos_del.append(i)

        if pos_del: peaks = np.delete(peaks, np.array(pos_del))
        if neg_del: neg_peaks = np.delete(neg_peaks, np.array(neg_del))

    elif mode == 'full':
        peaks, _ = sig.find_peaks(bvp)
        neg_peaks, _ = sig.find_peaks(-1 * bvp)

    # get zero crossings
    signs = np.sign(bvp)
    zc = np.where(np.diff(signs) != 0)[0] + 1

    # correct if there is a zc after last peak
    if peaks[-1] < zc[-1] and neg_peaks[-1] > peaks[-1]:
        if bvp[-1] > bvp[peaks[-1]]:
            peaks = np.append(peaks, bvp.size -1)
        else:
            peaks = np.append(peaks, peaks[-1])
    if neg_peaks[-1] < zc[-1] and peaks[-1] > neg_peaks[-1]:
        if bvp[-1] < bvp[neg_peaks[-1]]:
            neg_peaks = np.append(neg_peaks, bvp.size -1)
        else:
            neg_peaks = np.append(neg_peaks, neg_peaks[-1])


    # get peaks magnitude values
    pos_mag = bvp[peaks] / max(np.abs(bvp))
    neg_mag = bvp[neg_peaks] / max(np.abs(bvp))

    # copy peak indices
    peaks_copy = peaks
    neg_peaks_copy = neg_peaks

    # set inital values
    if peaks_copy[0] < neg_peaks_copy[0]:
        animation_state = [1]
        curr_mag = [bvp[peaks_copy[0]]]
    else:
        animation_state = [0]
        curr_mag = [-bvp[neg_peaks_copy[0]]]

    b = 0 #initial value for multiplying the pi that will be added with every reached peak
    c = 1 #initial value for the sign that changes with every reached peak

    animation_value = [ np.arcsin(bvp[0] / abs(curr_mag[-1])) ] #Problem for pixel with phase unequal to 0

    for i in range (1, bvp.size):
        if i in zc:
            if i < peaks[0] and i < neg_peaks[0]: curr_mag.append(curr_mag[-1]) #catch zero crossing before first peak
            # elif peaks_copy.size == 0 and neg_peaks_copy.size == 0: curr_mag.append(curr_mag[-1]) # catch zero crossing after last peak
            elif animation_state[-1] == 0: curr_mag.append(-bvp[neg_peaks_copy[0]])
            elif animation_state[-1] == 1: curr_mag.append(bvp[peaks_copy[0]])

        else:
            curr_mag.append(curr_mag[-1])

        # update ANIMATION VALUE
        b = addFunction(b, i, peaks_copy, neg_peaks_copy)
        c = signFunction(c, i, peaks_copy, neg_peaks_copy)

        if bvp[i] > curr_mag[-1] and bvp[i] > 0:
            raise RuntimeError(f"{bvp[i]}, {curr_mag[-1]}")
        elif bvp[i] < - curr_mag[-1] and bvp[i] < 0:
            raise RuntimeError(f"{bvp[i]}, {curr_mag[-1]}")

        av = np.arcsin(bvp[i] / abs(curr_mag[-1])) * c + b * np.pi * sign(peaks, neg_peaks)
        animation_value.append(av)

        if i in peaks_copy:
            animation_state.append(0)
            peaks_copy = np.delete(peaks_copy, 0)
        elif i in neg_peaks_copy:
            animation_state.append(1)
            neg_peaks_copy = np.delete(neg_peaks_copy, 0)
        else:
            animation_state.append(animation_state[-1])

        if len(animation_value) != len(curr_mag):
            raise RuntimeError(f"{animation_value} != {curr_mag} at {i}")

    #verifyAnimation(bvp, time, peaks, neg_peaks, np.array(animation_value), np.array(curr_mag), zc)

    return animation_value, curr_mag/np.max(curr_mag), time

def verifyAnimation(bvp, animation_value, curr_mag, time):
    """
    method that confirms that my animation and amplitude value algorithm works correctly
    :param bvp: bvp/ppg signal
    :param animation_value: value that controls the animation in Blender
    :param curr_mag: amplitude/magnitude value for each index of animation value signal
    :param time: time signal
    :return: -
    """

    sim_bvp = curr_mag * np.sin(animation_value)
    bvp = bvp / np.max(np.abs(bvp))

    if sim_bvp.size != bvp.size:
        raise AttributeError("Array length mismatch")

    """plt.plot(time, sim_bvp, 'r', label='simulated BVP')
    plt.plot(time, bvp, label='real BVP')
    #plt.plot(time[peaks], bvp[peaks], 'ro')
    #plt.plot(time[neg_peaks], bvp[neg_peaks], 'go')
    #plt.plot(time[zc], bvp[zc], 'rx')
    plt.legend()
    plt.title(f'NMAE: {np.sum(np.abs(bvp - sim_bvp)) / bvp.size / np.std(bvp)}')
    plt.show()"""

    x = bvp - sim_bvp
    print(f'summed Error: {np.sum(np.abs(bvp - sim_bvp))}')
    print(f'Array size: {bvp.size}')
    print(f'BVp std: {np.std(bvp)}')
    print(f"NMAE: {np.sum(np.abs(bvp - sim_bvp)) / bvp.size / np.std(bvp)}")

    return np.sum(np.abs(bvp - sim_bvp)) / bvp.size / np.std(bvp)

    #plt.plot(time, residual)
    #plt.plot(time[peaks], residual[peaks], 'ro')
    #plt.plot(time[neg_peaks], residual[neg_peaks], 'go')
    #plt.plot(time[zc], residual[zc], 'rx')
    #plt.show()


if __name__ == '__main__':
    time, bvp = readPPG(r"X:\PPGI\KISMED\p001.zip", "v01")
    avs, mags, time = getKeyframes(time, bvp)
    verifyAnimation(bvp, avs, mags, time)


