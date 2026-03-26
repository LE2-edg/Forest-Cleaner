"""Download long wind ambient from OpenGameArt."""
import urllib.request, os, wave

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ambient_wind_long.wav")
url = "https://opengameart.org/sites/default/files/wind%20background%20noise%202.wav"

if not os.path.exists(dest):
    print("Downloading mild wind background (CC0, Bashar3A from OpenGameArt)...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=120).read()
    with open(dest, "wb") as f:
        f.write(data)
    print(f"Saved: {dest} ({len(data)} bytes)")
else:
    print(f"Already exists: {dest} ({os.path.getsize(dest)} bytes)")

with wave.open(dest, "r") as wf:
    frames = wf.getnframes()
    rate = wf.getframerate()
    dur = frames / rate
    print(f"Duration: {dur:.1f}s, Rate: {rate}, Channels: {wf.getnchannels()}")
