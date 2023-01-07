![](http://neurojson.org/wiki/upload/blenderphotonics_header.png)

BlenderPhotonics
========================

-   **Author**: Qianqian Fang (q.fang at neu.edu) and Yuxuan Zhang (zhang.yuxuan1 at northeastern.edu)
-   **License**: GNU General Public License version 3 (GPLv3)
-   **Version**: v2023 (Beta)
-   **Website**: <http://mcx.space/BlenderPhotonics>
-   **Acknowledgement**: This project is funded by NIH awards 
      [R01-GM114365](https://grantome.com/grant/NIH/R01-GM114365-06) and 
      [U24-NS124027](https://reporter.nih.gov/search/dXkcyoaEQkaRrkpQoOnEBw/project-details/10308329)

Introduction
-------------
BlenderPhotonics_MCX is variation of BlenderPhotonics. In this branch, we replace `mmc` with `mcx` and use
vdb file as default model file format. Unfortunately, Blender does not integrate `pyopenvdb` into native python,
so you will need to manually compile `pyopenvdb` and add it to your python environment. We plan to release the 
official version after blender integrates pyopenvdb.

Installation
-------------
1. install `oct2py` and `jdata` to blender native python
2. compile `mcx` and then add `mcx` and `iso2mesh` to octave work path
3. install `pyopenvdb` to blender native python
4. download `BlenderPhotonics_MCX` as zip file and install in Blender

Tips1:\
The easiest way to install python packages for blender native python is to type code in script view in blender. 
First run
```angular2html
import sys
sys.path
```
You will see a list of blender native python environment path. Select one which you have write permission and then run: 
```
import subprocess
import sys
# enable pip
subprocess.call([sys.executable, "-m", "ensurepip"])
# upgrade pip to latest version
subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
# install any package
subprocess.call([sys.executable, "-m", "pip", "install", "oct2py", "--target=/Path/you/selected"])
subprocess.call([sys.executable, "-m", "pip", "install", "jdata", "--target=/Path/you/selected"])
```

Tips2:\
How to install `pyopenvdb` is not part of this tool. But if you can't wait for the new release of blender, you will need 
linux system, make, cmake (strong link recommended with GUI) and boost python. (I am working on a tutorial on how to 
install pyopenvdb and will post it in the future.)

![](http://neurojson.org/wiki/upload/blenderphotonics_install.png)

Real Machine Demo
-------------
Some screen shoot in IMG folder.