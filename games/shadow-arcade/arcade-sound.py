import math, os, shutil, struct, subprocess, time, wave
from pathlib import Path

class Sound:
    NOTES = {
        "launch": (160, 420, .22), "bumper": (430, 210, .10),
        "target": (580, 850, .14), "ramp": (340, 870, .24),
        "mission": (490, 980, .35), "drain": (270, 100, .22),
    }

    def __init__(self):
        self.player = "winsound" if os.name == "nt" else shutil.which("paplay")
        self.processes = []
        self.last_played = 0
        self.folder = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "shadow-arcade"
        if not self.player:
            return
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            for name, (start, end, duration) in self.NOTES.items():
                phase = 0
                frames = bytearray()
                count = int(22050 * duration)
                for i in range(count):
                    progress = i / count
                    phase += math.tau * (start + (end-start)*progress) / 22050
                    envelope = min(1, progress*45) * (1-progress)**2
                    signal = (math.sin(phase) + .24*math.sin(2*phase)) * envelope
                    frames.extend(struct.pack("<h", int(4500*signal)))
                with wave.open(str(self.folder / (name + ".wav")), "wb") as clip:
                    clip.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
                    clip.writeframes(frames)
        except OSError:
            self.player = None

    def play(self, name):
        now = time.monotonic()
        self.processes = [process for process in self.processes if process.poll() is None]
        if not self.player or len(self.processes) >= 3 or now-self.last_played < .055:
            return
        try:
            if self.player == "winsound":
                import winsound
                winsound.PlaySound(str(self.folder / (name + ".wav")), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                self.last_played = now
                return
            process = subprocess.Popen([self.player, str(self.folder / (name + ".wav"))],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processes.append(process)
            self.last_played = now
        except (OSError, RuntimeError):
            self.player = None


