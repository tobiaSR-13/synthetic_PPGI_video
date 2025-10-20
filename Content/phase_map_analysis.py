import numpy as np
import cv2

def main():
    phase_green = cv2.imread(r"Z:\dataset\processed\forexport\forexport\S01\textured_models\S01_moco_phase_g_hd.png", cv2.IMREAD_GRAYSCALE)
    phase_red = cv2.imread(r"Z:\dataset\processed\forexport\forexport\S01\textured_models\S01_moco_phase_r_hd.png", cv2.IMREAD_GRAYSCALE)
    phase_blue = cv2.imread(r"Z:\dataset\processed\forexport\forexport\S01\textured_models\S01_moco_phase_b_hd.png", cv2.IMREAD_GRAYSCALE)

    phase_green = np.astype(phase_green, np.int16)
    phase_blue = np.astype(phase_blue, np.int16)
    phase_red = np.astype(phase_red, np.int16)

    diff_gr = phase_green - phase_red
    diff_gb = phase_green - phase_blue

    print(
        f"Differences between Green and Red: -Max: {np.max(diff_gr)} -Min: {np.min(diff_gr)} -Mean: {np.mean(diff_gr)} -Std: {np.std(diff_gr)}")
    print(
        f"Differences between Green and Red: -Max: {np.max(diff_gb)} -Min: {np.min(diff_gb)} -Mean: {np.mean(diff_gb)} -Std: {np.std(diff_gb)}")

    diff_gr = np.astype(diff_gr, np.uint8)
    diff_gb = np.astype(diff_gb, np.uint8)

    cv2.imshow("GR", diff_gr)
    cv2.waitKey(0)
    cv2.imshow("GB", diff_gb)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()