import cv2
import numpy as np
import bpy
import os

from pathlib import Path


AIM_SIZE = 8192


def getRGB(rgb_image):
    """
    get each channel seperated from image
    :param rgb_image: image
    :return: red, green, blue, and alpha channel of rgb_image
    """
    channels = rgb_image.channels
    pixels = rgb_image.pixels[:]

    red = pixels[0::channels]
    green = pixels[1::channels]
    blue = pixels[2::channels]
    alpha = pixels[3::channels]

    return red, green, blue, alpha


def BW2OneChannel(bw_image):
    """
    make a black-white image that is loaded as a 3-channel image to a 1-channel image
    :param bw_image:
    :return:
    """
    channels = bw_image.channels
    pixels = bw_image.pixels[:]

    return pixels[0::channels]


# old method: is now done in shader editor
def mixColorAmplitude(color, amplitude):
    if not len(color) == len(amplitude):
        raise AttributeError(
            f"Color and Magnitude/Amplitude Map have unequal length ({len(color)} and {len(amplitude)})")

    color = np.asarray(color)
    amplitude = np.asarray(amplitude)

    low = color - amplitude
    high = color + amplitude

    return low, high


def prepareAmplitudeMaps(texture, ampl_red, ampl_green, ampl_blue, images):
    """
    prepare the maps that are needed for the amplitude
    :param texture: rgb image of skin texture
    :param ampl_red: red magnitude map
    :param ampl_green: green magnitude map
    :param ampl_blue: blue magnitude map
    :param images: Images class object (from config) for saving the images
    :return: Images class object that includes the amplitude and mean maps
    """
    red, green, blue, __ = getRGB(texture)

    images.addMean(array2bpyImage(red, "Red_mean"),
                   array2bpyImage(green, "Green_mean"),
                   array2bpyImage(blue, "Blue_mean")
                   )
    images.addMagnitudes(ampl_red, ampl_green, ampl_blue)

    return images


def array2bpyImage(image_arr, name):
    """
    make a 1-channel numpy array image to a bpy image
    :param image_arr: numpy array of image
    :param name: name for the bpy-image
    :return: image in bpy format
    """
    image_arr = np.asarray(image_arr)
    w = h = np.sqrt(image_arr.size)

    new_image = np.array([image_arr, image_arr, image_arr, np.ones_like(image_arr)])
    new_image = new_image.flatten()

    bpy_image = bpy.data.images.new(name=name, width=int(w), height=int(h), alpha=True, float_buffer=True)
    bpy_image.pixels = new_image.tolist()
    bpy_image.use_fake_user = True

    return bpy_image


def images2video(dir, settings):
    """
    make images in directory to a video
    :param dir: directory of the images
    :param name: name of the video that will be saved
    :param settings: RenderSettings object (from config)
    :return: -
    """

    output_path = os.path.join(dir, settings.video_file_name)
    dir = Path(dir)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, settings.fps, settings.resolution)

    for file in dir.iterdir():
        img = cv2.imread(file)
        video_writer.write(img)

    video_writer.release()

    print(f"Video saved in {output_path}")
