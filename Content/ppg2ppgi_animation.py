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

    # get zero crossings
    signs = np.sign(bvp)
    zc = np.where(np.diff(signs) != 0)[0] + 1

    peaks, neg_peaks = [], []
    last_zc = 0
    for z in zc:
        if signs[z-1] == 1:
            peak = np.argmax(bvp[last_zc:z]) + last_zc
            peaks.append(peak)
            last_zc = z
        elif signs[z-1] == -1:
            peak = np.argmin(bvp[last_zc:z]) + last_zc
            neg_peaks.append(peak)
            last_zc = z
        if z == zc[-1]:
            if signs[z] == 1:
                peak = np.argmax(bvp[z:]) + last_zc
                if bvp[peak] > bvp[peaks[-1]]: peaks.append(peak)
                else: peaks.append(peaks[-1])

            elif signs[z] == -1:
                peak = np.argmin(bvp[z:]) + last_zc
                if bvp[peak] < bvp[peaks[-1]]: neg_peaks.append(peak)
                else: neg_peaks.append(peaks[-1])

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

    # remove peak if it has index 0
    if 0 in peaks_copy:
        peaks_copy.remove(0)
    if 0 in neg_peaks_copy:
        neg_peaks_copy.remove(0)

    b = 0 #initial value for multiplying the pi that will be added with every reached peak
    c = 1 #initial value for the sign that changes with every reached peak

    animation_value = [ np.arcsin(bvp[0] / abs(curr_mag[-1])) ] #Problem for pixel with phase unequal to 0

    for i in range (1, bvp.size):
        if i in zc:
            if signs[i] == 1:
                curr_mag.append(bvp[peaks_copy[0]])
            elif signs[i] == -1:
                curr_mag.append(-bvp[neg_peaks_copy[0]])

        else:
            curr_mag.append(curr_mag[-1])

        # update ANIMATION VALUE
        b = addFunction(b, i, peaks_copy, neg_peaks_copy)
        c = signFunction(c, i, peaks_copy, neg_peaks_copy)

        if bvp[i] > curr_mag[-1] and bvp[i] > 0:
            raise RuntimeError(f"{bvp[i]}, {curr_mag[-1]} at {i}")
        elif bvp[i] < - curr_mag[-1] and bvp[i] < 0:
            raise RuntimeError(f"{bvp[i]}, {curr_mag[-1]} at {i}")

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


