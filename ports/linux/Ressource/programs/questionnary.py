import customtkinter as ctk
import json
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(os.path.dirname(CURRENT_DIR), 'data', 'data.json')
LANGUAGES_FILE = os.path.join(os.path.dirname(CURRENT_DIR), 'data', 'languages.json')

def save_language(lang_code, root):
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: pass
    
    data["language_selected"] = lang_code
    
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    root.destroy() 

def main():
    app = ctk.CTk()
    app.geometry("800x500")
    app.title("Select Language")
    
    ctk.CTkLabel(app, text="Bienvenue / Welcome", font=("Arial", 30)).pack(pady=50)
    
    langs = {"fr": "Français", "en": "English", "es": "Español"}
    try:
        with open(LANGUAGES_FILE, 'r', encoding='utf-8') as f:
            file_langs = json.load(f)
            langs = {k: v.get("language_name", k) for k, v in file_langs.items()}
    except: pass

    frame = ctk.CTkFrame(app)
    frame.pack(pady=20)

    for code, name in langs.items():
        ctk.CTkButton(frame, text=name, width=200, height=50, 
                      command=lambda c=code: save_language(c, app)).pack(pady=10)

    app.mainloop()

if __name__ == "__main__":
    main()