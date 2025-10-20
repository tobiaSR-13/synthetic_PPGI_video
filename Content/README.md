# Blender Synthetic Face Simulation


## Install

1. Alternative
Run the following command, maybe you need to execute the Terminal as **Admin**:
```
/path/to/blender/4.5/python/bin/python.exe -m pip install pandas opencv-python --no-cache-dir --target=/path/to/blender/4.5/python/lib/site-packages
```

`--target` was important for Blender 4.4 because otherwise it could be installed in a different python path than the Blender Python environment. Since I use 4.5 the installation only works if `--target` is not used. Sometimes, you have to restart Blender first before your changes work properly.

2. Alternative 

```
import pip
pip.main(['install','pandas==1.4.0'])
pip.main(['install','opencv-python'])
```

## Run in Blender
1. Open video_generation.py in Blender Text Editor
2. Change line 16 to your project directory
3. Change line 28 (`PPG_DATA_PATH`) to your PPG data path (should be the same if XDatabase directory of NAS is also mounted as `X:\`)
4. Run the file

For longer video rendering start Blender with command line tool in background, thus that no GUI is opened.
```
blender -b -p path/to/project/video_generation.py
```
Note that the directory to blender.exe has to be in your system environment variables.

## Run externally
```
blender -b -p path/to/project/external_video_generation.py
```
Give attention to the needed and optional positional arguments:
```
Make synthetic PPGI video with Blender in background.

positional arguments:
  map_subject          From which subject the magnitude and phase maps should be used.
  signal_subject       From which subject reference PPG signal should be used.
  signal_trial         From which trial reference PPG signal should be used.

options:
  -h, --help           show this help message and exit
  -s, --scamps         whether to use the rebuild of SCAMPS PPGI synthetic video generation.
  --ppg_path PPG_PATH  Path to directory where the real PPG signals (KISMED-dataset) are stored.
```