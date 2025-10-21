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

mag_scale = 1


