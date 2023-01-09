#!/bin/bash
#================================================================================================
# Bash shell script to install BlenderPhotonics and all dependencies
#================================================================================================
# installing software and python modules and their dependencies
# (replace "apt" in the line below by "yum" on Fedora Linux, or "port" on Mac OS)
#================================================================================================
sudo apt install 'blender' 'octave' 'wget' 'unzip'                    # install software
BPY=`blender -b --python-expr 'import sys;print(sys.executable)'|grep 'python'` #blender's python
"$BPY" -m ensurepip                                                   # enable pip package
"$BPY" -m pip install 'oct2py' 'jdata' 'bjdata' 'wheel'               # install Python modules
#================================================================================================
# download and install octave/matlab toolboxes (replace wget URLs by those of newer releases)
#================================================================================================
mkdir -p "$HOME/blenderphotonics" && cd "$HOME/blenderphotonics"      # create toolbox folder
GH=https://github.com
wget "$GH/fangq/iso2mesh/releases/download/v1.9.6/iso2mesh-1.9.6-allinone.zip" #iso2mesh toolbox
wget "$GH/fangq/zmat/releases/download/v0.9.8/zmat-0.9.8-allinone.zip"         #zmat toolbox
wget http://mcx.space/nightly/release/v2020/mmclab-linux-x86_64-v2020.zip      #mmclab toolbox
find . -name "*.zip" -exec unzip '{}' \;                              # unzip toolboxes
rm -rf "$HOME/blenderphotonics/*.zip"                                 # remove downloaded files
echo "addpath(genpath('$HOME/blenderphotonics'));">>"$HOME/.octaverc" # add path to toolboxes
#================================================================================================
# donwload and install BlenderPhotonics add-on (replace wget URLs by those of newer releases)
#================================================================================================
BLENDERVER=`blender -v | grep -oh '\b[0-9]\+\.[0-9]\+'`               # obtain blender version
BLENDERADDON="$HOME/.config/blender/$BLENDERVER/scripts/addons"       # get blender addon folder
mkdir -p "$BLENDERADDON"                                              # create addon folder
cd "$BLENDERADDON"
wget "$GH/COTILab/BlenderPhotonics/releases/download/v2022pre/BlenderPhotonics-v2022preview.zip"
unzip BlenderPhotonics-v2022preview.zip                               # install addon
#================================================================================================
# verification
#================================================================================================
blender -b --python-expr 'import oct2py;import jdata;import bjdata;'  # should show no error
octave-cli --eval "which s2m mmc zmat"                                # should print the paths
