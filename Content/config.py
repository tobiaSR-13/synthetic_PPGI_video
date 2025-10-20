try:
    from image_prep import getRGB
except ModuleNotFoundError:
    pass #to avoid problems with bpy library when testing only this file
import numpy as np
#import robustsp as rs
from m_estimator import huber_m_estimator
import os


# names for animation and magnitude value nodes
av_name = "AV"

mag_name = "MAG"

# path of this file and project directory
path = os.path.dirname(os.path.abspath(__file__))

# differnt scenarios for different light settings
scenario = {"1a": {"top_light": 1, "side_light": 0, "translation": False, "rotation": False},
            "1b": {"top_light": 0, "side_light": 0, "translation": False, "rotation": False},
            "1c": {"top_light": 0.5, "side_light": 0, "translation": False, "rotation": False},
            "2a": {"top_light": 1, "side_light": 1, "translation": False, "rotation": False},
            "2b": {"top_light": 0, "side_light": 1, "translation": False, "rotation": False},
            "3a": {"top_light": 1, "side_light": 0, "translation": True, "rotation": False},
            "3b": {"top_light": 1, "side_light": 0, "translation": False, "rotation": True},
            "3c": {"top_light": 1, "side_light": 0, "translation": True, "rotation": True},
            #"4": {"top_light": 1, "side_light": 0, "translation": False, "rotation": False},
            #"5": {"top_light": 1, "side_light": 0, "translation": False, "rotation": False},
            #"6": {"top_light": 1, "side_light": 0, "translation": False, "rotation": False},
            #"7": {"top_light": 1, "side_light": 0, "translation": False, "rotation": False}
            }

# names for important existing materials and nodes
TL_name = "Material.023"
TL_node = "Emission"
TL_value = 20

SL_name = "Baustrahler_light"
SL_node = "Emission"
SL_value = 60

# environment light setting
sunlight = (244/256, 233/256, 155/256, 1)
sunstrength = 3

# SCAMPS mean radius setting
red_radius = 0.36
green_radius = 0.41
blue_radius = 0.23

SUBSURFACE_FAC = 0.1

# Subjects of several Datasets
map_subjects = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12","S13", "S14", "S15"]

kismed_ppgi = ["p001", "p002", "p003", "p004", "p005", "p006", "p007", "p008", "p009", "p010"]



# subclass to save all important images for shader editor
class Images:

    def __init__(self):
        self.texture = None

        self.phase_green = None
        self.phase_red = None
        self.phase_blue = None
        self.magnitude_blue = None
        self.magnitude_red = None
        self.magnitude_green = None
        self.mean_blue = None
        self.mean_red = None
        self.mean_green = None

        self.scamps_mask = None

    # add texture image
    def addTexture(self, tex):
        self.texture = tex

    # add phase maps for R, G, and B
    def addPhases(self, red, green, blue):
        self.phase_red = red
        self.phase_green = green
        self.phase_blue = blue

    # add magnitude maps for R, G, and B
    def addMagnitudes(self, red, green, blue):
        self.magnitude_red = red
        self.magnitude_green = green
        self.magnitude_blue = blue

    # add the mean color during the animation
    def addMean(self, red, green, blue):
        self.mean_red = red
        self.mean_green = green
        self.mean_blue = blue

    # add SCAMPS mask
    def addSCAMPS(self, scamps):
        self.scamps_mask = scamps

    # compute the mean skin color of the texture
    # Huber's m-estimator is used to compute the mean skin color because of disturbing distributions from eyes, lips and hair colors
    def getMeanSkinColor(self):

        if self.texture == None:
            raise RuntimeError("You need a stored texture image to get mean skin colors.")
        red, green, blue, _ = getRGB(self.texture)

        red = np.asarray(red).flatten()
        green = np.asarray(green).flatten()
        blue = np.asarray(blue).flatten()

        mean_red = huber_m_estimator(red)
        mean_green = huber_m_estimator(green)
        mean_blue = huber_m_estimator(blue)

        #print(np.mean(red))
        #print(np.mean(green))
        #print(np.mean(blue))

        return (mean_red, mean_green, mean_blue, 1)
