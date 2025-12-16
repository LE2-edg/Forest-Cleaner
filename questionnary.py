def tkinter_installer():
    pass

def tkinter_analyser():
    try:
        with open ("tkinter_analyse.py", 'r', UTF-8) as tka:
            if tkinter_is_present == False:
                return tkinter_installer
            else: return True
    finally: return tkinter_path


def main():
    if tkinter_analyser == tkinter_path:
        ask_languages
    