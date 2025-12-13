import json
import os
import sys
import subprocess

DATA_FOLDER = 'Ressource/data'
DATA_FILENAME = 'data.json'
DATA_FILEPATH = os.path.join(DATA_FOLDER, DATA_FILENAME)

language_key = "language_selected"
programs = 'programs/'
questionnary = "questionnary.py"
initiale_main = "programs/initiale_main.py"
imp = initiale_main


def questionnare_launch():
    return os.path.join(programs, questionnary)

def initial_launch():
    return imp

def tkinter_installed():
    """Cette fonction sert à vérifier si tkinter est installé ou pas"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def tkinter_installer():
    """Installe tkinter en utilisant pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinter"])
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def customtkinter_installed():
    """Vérifie si le module customtkinter est installé."""
    try:
        import customtkinter
        return True
    except ImportError:
        return False

def customtkinter_installer():
    """Installe customtkinter en utilisant pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def main():
    if tkinter_installed() == False:
        tkinter_installer()
    if customtkinter_installed() == False:
        customtkinter_installer()

    with open(DATA_FILEPATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if language_key in data and data.get(language_key) is not None:
        return initial_launch()
    else:
        return questionnare_launch()

if __name__ == "__main__":
    main()