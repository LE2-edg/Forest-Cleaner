"""Check audio file durations using Panda3D, then test playback."""
import os, sys
from ursina import Ursina
app = Ursina(window_type='none')
from panda3d.core import AudioSound, Filename

test_dir = os.path.dirname(os.path.abspath(__file__))

files = [
    'ambient_wind_long.wav',
    'ambient_cicadas.mp3',
    'ambient_birds.mp3',
    'wind.ogg',
    'wind2.ogg',
    'wind3.ogg',
]

for f in files:
    fp = os.path.join(test_dir, f)
    if not os.path.exists(fp):
        print(f"{f}: NOT FOUND")
        continue
    sfx = loader.loadSfx(Filename.fromOsSpecific(fp))
    status = sfx.status()
    length = sfx.length()
    size_kb = os.path.getsize(fp) // 1024
    ok = "OK" if status != AudioSound.BAD else "BAD"
    print(f"{f}: {ok}, {length:.1f}s, {size_kb}KB")

app.destroy()
