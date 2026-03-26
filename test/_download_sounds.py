"""Download long CC0 nature ambient sounds for Forest Cleaner."""
import urllib.request
import re
import os

DEST = os.path.dirname(os.path.abspath(__file__))

def download(url, filename):
    dest_path = os.path.join(DEST, filename)
    if os.path.exists(dest_path):
        print(f"  Already exists: {filename} ({os.path.getsize(dest_path)} bytes)")
        return True
    print(f"  Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        with open(dest_path, "wb") as f:
            f.write(data)
        print(f"  Saved: {filename} ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

# --- Internet Archive: list files from the nature sounds album ---
print("=== Checking Internet Archive album ===")
try:
    req = urllib.request.Request(
        "https://archive.org/download/ua-wake-up-with-nature-2000-opus-48/",
        headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    ogg_files = re.findall(r'href="([^"]+\.ogg)"', html)
    for f in ogg_files:
        print(f"  Found: {f}")
except Exception as e:
    print(f"  Error listing: {e}")
    ogg_files = []

# --- Download two long ambient tracks ---
# 1) Long forest wind + birds from Pixabay (Eryliaa, Pixabay license - free for any use)
#    These are on CDN but need API. Let's try direct OGG from archive.org

# Try the serene forest track
if ogg_files:
    for og in ogg_files:
        if "forest" in og.lower() or "serene" in og.lower() or "nature" in og.lower():
            base_url = "https://archive.org/download/ua-wake-up-with-nature-2000-opus-48/"
            download(base_url + og, "ambient_forest_long.ogg")
            break

# 2) Also try freesound CC0 content via direct links
# Freesound user 'klankbeeld' has many CC0 field recordings
# Let's try a known CC0 wind recording from Internet Archive
print("\n=== Downloading from known CC0 sources ===")

# Long gentle wind - from archive.org (public domain nature sounds collection)
download(
    "https://archive.org/download/summertime-cicadas-texas-nature-sounds/Summertime%20Cicadas%2C%20Texas%2C%20Nature%20Sounds.mp3",
    "ambient_cicadas.mp3"
)

# Check all ambient files we have
print("\n=== Current ambient files ===")
for f in sorted(os.listdir(DEST)):
    if f.startswith("ambient") or f.startswith("wind"):
        fp = os.path.join(DEST, f)
        print(f"  {f}: {os.path.getsize(fp)} bytes")
