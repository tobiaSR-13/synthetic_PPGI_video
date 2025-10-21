import numpy as np
from image_prep import getRGB, getMax
from m_estimator import huber_m_estimator

# class to save all important images for shader editor
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

        self.max_mag_red = getMax(red)
        self.max_mag_green = getMax(green)
        self.max_mag_blue = getMax(blue)

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