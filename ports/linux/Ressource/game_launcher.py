
import sys
import os
import subprocess

necesary_modules = ["lvgl"]

def installationist():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lvgl"])

installationist()

import lvgl as lv

root = lv.lv
