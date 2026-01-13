
import sys
import os
import subprocess

necesary_modules = ["lvgl"]

def installationist():
    try:
        for e in necesary_modules:
            import e
    except ImportError:
        print(terminal_question_admin)
        subprocess.check_call([sys.executable, "sudo", "apt", "install", e])

installationist()

import lvgl as lv

void main()
{
    lv_button_label
}
