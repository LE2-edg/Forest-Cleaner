import lvgl as lv
import os
import sys

reg = 0
def languages_opener()
    with open("languages.json", "r", encoding= UTF-8):
        return languages

def main_page():
    pass

def check_os():
    pass

def parameters_pop_up():
    pass

def registration_page():
    imp = languages_opener()
    name_ask = 

def all_parameters():
    os = ""
    version = None
    check_os(os, version)
    if os == "android":
        if 8< version < 12:
            pass
    if os == "ios":
        if 12< version < 18:
            pass

def registrated():
    if reg == 1:
        return True

def main():
    if registrated() == True:
        if all_parameters() == True:
            main_page()
        else:
            parameters_pop_up()
    else:
        registration_page()

main()
