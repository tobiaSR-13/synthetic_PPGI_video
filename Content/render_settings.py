import os

# class to save different render settings
class RenderSettings:

    # initialize
    def __init__(self, camera, map_subject, ppg_subject, ppg_trial, scamps, sf, ef):
        self.start_frame = sf
        self.end_frame = ef
        self.fps = 30
        self.camera = camera

        if camera == "Logitech":
            self.resolution = (1280, 960)
        elif camera == "Sigma":
            self.resolution = (3840, 2180)

        self.denoiser = 'OPTIX'
        self.samples = 256
        self.engine = 'CYCLES'
        self.device = 'GPU'
        self.cdt = 'OPTIX' # compute Device Type
        self.device_name = None

        if scamps:
            self.video_file_name = f"{map_subject}_PPG{ppg_subject}_{ppg_trial}_scamps.mp4"
        else:
            self.video_file_name = f"{map_subject}_PPG{ppg_subject}_{ppg_trial}.mp4"

        self.scamps = scamps
        self.map_subject = map_subject
        self.ppg_subject = ppg_subject
        self.ppg_trial = ppg_trial

    # set last frame (during the animation is defined)
    def adjustEndFrame(self, end_frame):
        if self.end_frame > end_frame:
            self.end_frame = end_frame

    def adjustDeviceName(self, device_name):
        self.device_name = device_name

    def writeLog(self, dir):

        log = ""

        log += f"Camera: {self.camera}\n"
        log += f"Frames: {self.start_frame} - {self.end_frame}\n"
        log += f"FPS: {self.fps}\n"
        log += f"Render Engine: {self.engine}\n"
        log += f"Compute Device Type: {self.cdt}\n"
        log += f"Device Name: {self.device_name}\n"
        log += f"Device: {self.device}\n"
        log += f"Samples: {self.samples}\n"
        log += f"Denoiser: {self.denoiser}\n"
        log += "\n"
        log += f"Map Subject: {self.map_subject}\n"
        log += f"PPG subject: {self.ppg_subject}\n"
        log += f"PPG Trial: {self.ppg_trial}\n"
        log += "Scamps Approach" if self.scamps else "Our Approach"

        with open(os.path.join(dir, "log.txt"), "w", encoding="utf-8") as file:
            file.write(log)
