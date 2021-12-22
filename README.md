# BlenderPhotonics
run mmc in blender

How to install:

1, Install Blender(2.8 or higher) and Octave(5.0 or lower) and add them to PATH

2, Install oct2py for Blender
  
  Open Blender and go to script view, text below commond and run.
  ```
  import subprocess
  import sys
  # enable pip
  subprocess.call([sys.executable, "-m", "ensurepip"])
  # upgrade pip to latest version
  subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
  # install any package
  subprocess.call([sys.executable, "-m", "pip", "install", "oct2py"])
  ```
  For Linux user, you can manually copy modules from /home/username/.local/lib/python3.9/site-packages to /home/username/.config/blender/2.93/scripts/modules
  
3, Complie MMC

  User should complie MMC for Octave and overwrite BlenderPhotonics's MMC folder (depend on user's system).
 
4, Restart Blender and enanble BlenderPhotonics

  Move BlenderPhotonics folder to blender script path. You can found path in 'https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html'. Then restart Blender and go to '' Edit --> Preference --> Add-ons'' and search "BlenderPhotonics". Enable it and you will see a interface named "BlenderPhotonics" in Layout view.
   
