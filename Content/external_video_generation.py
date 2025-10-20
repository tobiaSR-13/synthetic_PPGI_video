import argparse
import config
import os
import bpy
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_generation import main
import image_prep as ip

if __name__ =="__main__":

    parser = argparse.ArgumentParser(description="Make synthetic PPGI video with Blender in background.")

    parser.add_argument("map_subject", help="From which subject the magnitude and phase maps should be used.")
    parser.add_argument("signal_subject", help="From which subject reference PPG signal should be used.")
    parser.add_argument("signal_trial", help="From which trial reference PPG signal should be used.")
    parser.add_argument("-s", "--scamps", action="store_true", help="whether to use the rebuild of SCAMPS PPGI synthetic video generation.")
    parser.add_argument("--ppg_path", default=r"X:\PPGI\KISMED", help="Path to directory where the real PPG signals (KISMED-dataset) are stored.")

    args = parser.parse_args()

    if args.map_subject not in config.map_subjects and not args.scamps:
        raise AttributeError(f"Named map subject must be in {config.map_subjects}")

    if args.signal_subject not in config.kismed_ppgi:
        raise AttributeError(f"Named ppg reference subject must be in {config.kismed_ppgi}")

    file = config.path

    # load files
    exp_room_path = os.path.join(file, r"ExpRoom_template.blend")
    uv_map_path = os.path.join(file, r"\assets\uv_coords_template.npy")

    # Images (from config) object to save images
    images = config.Images()

    # load skin texture
    tex_image = bpy.data.images.load(os.path.join(file, r"assets\tex_sample_01.png"), check_existing=True)
    tex_image.use_fake_user = True
    images.addTexture(tex_image)

    if args. scamps: # load SCAMPS mask
        scamps_mask = bpy.data.images.load(os.path.join(file, r"assets\SCAMPS_mask.png"),
                                           check_existing=True)
        scamps_mask.use_fake_user = True
        images.addSCAMPS(scamps_mask)

    else: # Load BVP maps
        phase_red = bpy.data.images.load(os.path.join(file, "assets", f"{args.map_subject}_moco_phase_r_hd.png"),
                                         check_existing=True)
        phase_red.use_fake_user = True
        mag_blue = bpy.data.images.load(os.path.join(file,"assets", f"{args.map_subject}_moco_mag_b_hd.png"),
                                        check_existing=True)
        mag_blue.use_fake_user = True
        mag_green = bpy.data.images.load(os.path.join(file,"assets", f"{args.map_subject}_moco_mag_g_hd.png"),
                                         check_existing=True)
        mag_green.use_fake_user = True
        mag_red = bpy.data.images.load(os.path.join(file,"assets", f"{args.map_subject}_moco_mag_r_hd.png"),
                                       check_existing=True)
        mag_red.use_fake_user = True
        phase_blue = bpy.data.images.load(os.path.join(file,"assets", f"{args.map_subject}_moco_phase_b_hd.png"),
                                          check_existing=True)
        phase_blue.use_fake_user = True
        phase_green = bpy.data.images.load(os.path.join(file,"assets", f"{args.map_subject}_moco_phase_g_hd.png"),
                                           check_existing=True)
        phase_green.use_fake_user = True

        images = ip.prepareAmplitudeMaps(tex_image, mag_red, mag_green, mag_blue, images)

        images.addPhases(phase_red, phase_green, phase_blue)

    #path for ppg signal of kismed dataset
    ppg_path = os.path.join(args.ppg_path, f"{args.signal_subject}.zip")

    #run main method
    main(exp_room_path, uv_map_path, images, args.scamps, args.map_subject, args.signal_subject, args.signal_trial)