#!/usr/bin/python3
"""Shadow Pinball, a local GTK/Cairo arcade game."""
import json
import math
import os
import shutil
import struct
import subprocess
import wave
import time
from dataclasses import dataclass
from pathlib import Path

import cairo
if os.name == "nt":
    from windows_game_ui import Gdk, GLib, Gtk
else:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk

WIDTH, HEIGHT = 530, 740
RADIUS = 7
STEP = 1 / 240
CYAN = (.22, .91, 1)
PINK = (1, .24, .68)
GOLD = (1, .72, .27)
LEFT_PIVOT, RIGHT_PIVOT, FLIPPER_Y = 150, 326, 635
FLIPPER_LENGTH = 76
RAIL = [(LEFT_PIVOT, 747), (LEFT_PIVOT, FLIPPER_Y), (67, 550),
        (25, 465), (25, 158), (54, 89), (121, 42), (305, 28),
        (411, 51), (477, 107), (508, 182), (508, 723), (466, 723)]
RETURN = [(RIGHT_PIVOT, 747), (RIGHT_PIVOT, FLIPPER_Y),
          (411, 550), (458, 465), (458, 195)]
SHOOTER_RAIL = ((458, 195), (458, 723))
GATE = ((458, 195), (508, 161))
SLINGS = [(69, 464, 122, 522, 1), (415, 464, 362, 522, -1)]
BUMPERS = [(146, 188, 29), (297, 190, 29), (222, 267, 35)]
ROLLOVERS = (115, 208, 301, 394)
TARGETS = [(72, 363), (90, 391), (108, 419), (369, 419), (388, 391), (407, 363)]
SAVE = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "shadow-pinball" / "scores.json"


@dataclass
class Ball:
    x: float = 483
    y: float = 690
    vx: float = 0
    vy: float = 0
    staged: bool = True
    gate: bool = False


class Table:
    def __init__(self):
        self.muted = False
        self.effects = []
        try:
            saved = json.loads(SAVE.read_text())
            self.best = max(0, int(saved.get("best", 0)))
            self.muted = saved.get("muted") is True
        except (OSError, ValueError, TypeError, AttributeError):
            self.best = 0
        self.reset()

    def reset(self):
        self.balls = [Ball()]
        self.remaining = 3
        self.score = 0
        self.hit = {}
        self.bank = set()
        self.rollovers = set()
        self.ramps = set()
        self.multiplier = 1
        self.ball_save = 0
        self.save_used = False
        self.shots = 0
        self.missions = 0
        self.multiball_used = False
        self.combo = 0
        self.last_hit = -10
        self.elapsed = 0
        self.message = "HOLD SPACE TO CHARGE"
        self.flash = 0
        self.charge = 0
        self.paused = False
        self.over = False
        self.keys = set()
        self.angles = [0.35, math.pi - 0.35]

    def save_score(self):
        self.best = max(self.best, self.score)
        try:
            SAVE.parent.mkdir(parents=True, exist_ok=True)
            temp = SAVE.with_suffix(".tmp")
            temp.write_text(json.dumps({"best": self.best, "muted": self.muted}) + "\n")
            temp.replace(SAVE)
        except OSError:
            self.message = "HIGH SCORE COULD NOT BE SAVED"

    def launch(self):
        if self.paused or self.over:
            return
        launched = False
        for ball in self.balls:
            if ball.staged:
                launched = True
                self.effects.append("launch")
                ball.staged = False
                ball.vy = -max(1030, 1120 + self.charge * 540)
                self.message = "LIGHT THE SIX DATA TARGETS"
        self.charge = 0
        if launched and not self.save_used:
            self.ball_save = self.elapsed + 6

    def award(self, value, label):
        self.combo = min(5, self.combo + 1) if self.elapsed - self.last_hit < 1.4 else 1
        self.last_hit = self.elapsed
        self.score += value * self.combo * self.multiplier
        self.effects.append({250: "bumper", 750: "target", 2400: "ramp", 10000: "mission"}.get(value, "target"))
        self.flash = .52
        self.message = label + (f" x{self.combo}" if self.combo > 1 else "")

    @staticmethod
    def segment(ball, ax, ay, bx, by, width=0, angular=0, bounce=.76):
        dx, dy = bx - ax, by - ay
        u = max(0, min(1, ((ball.x - ax) * dx + (ball.y - ay) * dy) / (dx*dx + dy*dy)))
        nx, ny = ball.x - ax - u*dx, ball.y - ay - u*dy
        dist = math.hypot(nx, ny)
        if not 0 < dist < RADIUS + width:
            return None
        nx, ny = nx/dist, ny/dist
        ball.x = ax + u*dx + nx*(RADIUS + width)
        ball.y = ay + u*dy + ny*(RADIUS + width)
        surface_vx, surface_vy = -angular*u*dy, angular*u*dx
        inward = (ball.vx-surface_vx)*nx + (ball.vy-surface_vy)*ny
        if inward < 0:
            ball.vx -= (1+bounce)*inward*nx
            ball.vy -= (1+bounce)*inward*ny
        return nx, ny, inward

    def flippers(self):
        for i, x in enumerate((LEFT_PIVOT, RIGHT_PIVOT)):
            angle = self.angles[i]
            yield x, FLIPPER_Y, x + math.cos(angle)*FLIPPER_LENGTH, FLIPPER_Y + math.sin(angle)*FLIPPER_LENGTH

    def advance(self):
        if self.paused or self.over:
            return
        self.elapsed += STEP
        self.flash = max(0, self.flash - STEP)
        if "space" in self.keys:
            self.charge = min(1, self.charge + STEP*1.25)
        speed = []
        for i, key in enumerate(("Shift_L", "Shift_R")):
            raised = key in self.keys
            aim = (-.59 if raised else .35) if i == 0 else (math.pi+.59 if raised else math.pi-.35)
            old = self.angles[i]
            self.angles[i] += max(-STEP*16, min(STEP*16, aim-old))
            speed.append((self.angles[i]-old)/STEP if raised else 0)

        for ball in self.balls[:]:
            if ball.staged:
                continue
            ball.vy += 725 * STEP
            velocity = math.hypot(ball.vx, ball.vy)
            if velocity > 1650:
                ball.vx *= 1650/velocity
                ball.vy *= 1650/velocity
            ball.x += ball.vx * STEP
            ball.y += ball.vy * STEP
            if ball.x > 466 and ball.y < 143 and not ball.gate:
                ball.vx = -max(255, abs(ball.vy)*.37)
                ball.gate = True
            for path in (RAIL, RETURN):
                for a, b in zip(path,path[1:]):
                    self.segment(ball,*a,*b,width=2,bounce=.55 if ball.y>465 else .77)
            self.segment(ball,*SHOOTER_RAIL[0],*SHOOTER_RAIL[1],width=2)
            if ball.gate:
                self.segment(ball,*GATE[0],*GATE[1],width=2,bounce=.62)
            for i,(ax,ay,bx,by,direction) in enumerate(SLINGS):
                hit=self.segment(ball,ax,ay,bx,by,width=3,bounce=.58)
                if hit and hit[0]*direction>.2 and hit[2]<-65 and self.elapsed-self.hit.get(20+i,-10)>.19:
                    self.hit[20+i]=self.elapsed
                    ball.vx+=direction*310
                    ball.vy-=240
                    self.award(100,"SLINGSHOT")
            for i,f in enumerate(self.flippers()):
                self.segment(ball,*f,width=6,angular=speed[i],bounce=.34)
            for i, (x, y, r) in enumerate(BUMPERS):
                dx, dy = ball.x-x, ball.y-y
                dist = math.hypot(dx, dy)
                if 0 < dist < r+RADIUS:
                    nx, ny = dx/dist, dy/dist
                    ball.x, ball.y = x+nx*(r+RADIUS), y+ny*(r+RADIUS)
                    force = max(470, math.hypot(ball.vx, ball.vy)*1.04)
                    ball.vx, ball.vy = nx*force, ny*force
                    if self.elapsed-self.hit.get(i,-10) > .16:
                        self.hit[i] = self.elapsed
                        self.award(250, "REACTOR HIT")
            for i, (x, y) in enumerate(TARGETS):
                if math.hypot(ball.x-x, ball.y-y) < 19 and i not in self.bank:
                    self.bank.add(i)
                    self.award(750, "DATA TARGET")
            for i, x in enumerate(ROLLOVERS):
                if abs(ball.x-x) < 19 and abs(ball.y-66) < 12 and i not in self.rollovers:
                    self.rollovers.add(i)
                    self.award(400, "UPLINK ROLLOVER")
            if len(self.rollovers) == len(ROLLOVERS):
                self.rollovers.clear()
                self.multiplier = min(5, self.multiplier + 1)
                self.award(2000, f"UPLINK COMPLETE | x{self.multiplier} SCORE")
            for i, x in enumerate((116, 342)):
                if abs(ball.x-x) < 23 and abs(ball.y-119) < 12 and ball.vy < -340 and self.elapsed-self.hit.get(10+i,-10)>1:
                    self.hit[10+i] = self.elapsed
                    self.ramps.add(i)
                    self.shots += 1
                    ball.x, ball.y = 228, 355
                    ball.vx, ball.vy = (-180 if i else 180), 190
                    self.award(2400, "OVERCLOCK RAMP")
            if ball.y > HEIGHT+12:
                self.balls.remove(ball)
        if len(self.bank) == len(TARGETS) and len(self.balls) == 1 and not self.multiball_used:
            self.multiball_used = True
            self.bank.clear()
            self.missions += 1
            self.award(10000, "BREACH COMPLETE | MULTIBALL")
            self.balls.extend((Ball(161, 465, -230, -460, False, True),
                               Ball(306, 465, 230, -460, False, True)))
            if self.missions % 2 == 0:
                self.remaining += 1
                self.message = "BREACH COMPLETE | EXTRA BALL"
        if not self.balls and self.elapsed < self.ball_save:
            self.ball_save = 0
            self.save_used = True
            self.balls.append(Ball())
            self.message = "BALL SAVED | RELAUNCH"
            return
        if not self.balls:
            self.effects.append("drain")
            self.remaining -= 1
            self.combo = 0
            if self.remaining:
                self.save_used = False
                self.multiball_used = False
                self.bank.clear()
                self.balls.append(Ball())
                self.message = "BALL LOST | HOLD SPACE TO LAUNCH"
            else:
                self.over = True
                self.message = "GAME OVER | ENTER TO PLAY AGAIN"
                self.save_score()


def text(ctx, x, y, label, size, rgb, bold=False):
    ctx.select_font_face("Sans", 0, int(bold))
    ctx.set_font_size(size)
    ctx.set_source_rgb(*rgb)
    ctx.move_to(x, y)
    ctx.show_text(label)


def line(ctx, points, rgb, width=2):
    ctx.set_source_rgb(*rgb)
    ctx.set_line_width(width)
    ctx.set_line_cap(1)
    ctx.set_line_join(1)
    ctx.move_to(*points[0])
    for point in points[1:]:
        ctx.line_to(*point)
    ctx.stroke()


def circle(ctx, x, y, r, rgb, alpha=1):
    ctx.set_source_rgba(*rgb, alpha)
    ctx.arc(x, y, r, 0, math.tau)
    ctx.fill()


def panel(ctx, x, y, w, h, fill, edge, cut=9):
    points = [(x+cut,y),(x+w-cut,y),(x+w,y+cut),(x+w,y+h-cut),
              (x+w-cut,y+h),(x+cut,y+h),(x,y+h-cut),(x,y+cut)]
    ctx.move_to(*points[0])
    for point in points[1:]:
        ctx.line_to(*point)
    ctx.close_path()
    ctx.set_source_rgb(*fill)
    ctx.fill_preserve()
    ctx.set_source_rgb(*edge)
    ctx.set_line_width(1)
    ctx.stroke()


def neon(ctx, points, color, core=2):
    for size, alpha in ((17,.035),(11,.07),(6,.19),(core,.93)):
        ctx.set_line_width(size)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgba(*color,alpha)
        ctx.move_to(*points[0])
        for point in points[1:]:
            ctx.line_to(*point)
        ctx.stroke()


def table_art(ctx):
    gradient = cairo.LinearGradient(0,0,WIDTH,HEIGHT)
    gradient.add_color_stop_rgb(0,.065,.15,.23)
    gradient.add_color_stop_rgb(.48,.055,.052,.127)
    gradient.add_color_stop_rgb(1,.14,.043,.13)
    ctx.set_source(gradient)
    ctx.rectangle(0,0,WIDTH,HEIGHT)
    ctx.fill()
    for x in range(8,WIDTH,16):
        line(ctx,[(x,0),(x,HEIGHT)],(.09,.13,.22),.65)
    for y in range(8,HEIGHT,16):
        line(ctx,[(0,y),(WIDTH,y)],(.09,.13,.22),.65)
    for side in (0,1):
        def flip(x):
            return WIDTH-x-57 if side else x
        for i in range(6):
            x,y=flip(31+i*9),98+i*43
            points=[(x,y),(x,y+64),(flip(94+i*13),y+128),
                    (flip(94+i*13),y+161),(flip(166+i*8),y+233)]
            line(ctx,points,(.15,.25,.36) if i%2 else (.29,.13,.31),1.1)
            circle(ctx,*points[-1],2,CYAN if i%2 else PINK,.64)
    for i in range(12):
        x=177+(i*29)%128
        y=453+(i*31)%120
        panel(ctx,x,y,10+(i%3)*4,9,(.10,.13,.22),(.21,.29,.41),2)
    for i in range(8):
        y=566+i*11
        line(ctx,[(198-i*2,y),(230,y),(268+i*2,y)],(.26,.12,.27),1)
    for x in (29,446,492):
        for y in (219,334,494,549):
            circle(ctx,x,y,5,(.08,.11,.16))
            circle(ctx,x,y,3,(.31,.39,.47))
            line(ctx,[(x-2,y-2),(x+2,y+2)],(.09,.13,.18),1)


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
        self.folder = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "shadow-pinball"
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


class Pinball(Gtk.Window):
    def __init__(self):
        super().__init__(title="Shadow Pinball")
        self.set_icon_name("shadow-pinball")
        self.set_default_size(770, 690)
        self.set_size_request(560, 490)
        self.table = Table()
        self.sound = Sound()
        self.art = cairo.ImageSurface(cairo.FORMAT_RGB24, WIDTH, HEIGHT)
        table_art(cairo.Context(self.art))
        self.clock = time.monotonic()
        self.accumulator = 0
        self.surface = Gtk.DrawingArea()
        self.add(self.surface)
        self.surface.connect("draw", self.draw)
        self.connect("key-press-event", self.press)
        self.connect("key-release-event", self.release)
        self.connect("focus-out-event", self.unfocus)
        self.connect("destroy", self.close)
        GLib.timeout_add(16, self.tick)
        self.show_all()

    def press(self, _, event):
        key = Gdk.keyval_name(event.keyval)
        if key in self.table.keys:
            return True
        self.table.keys.add(key)
        if key in ("Escape", "p", "P"):
            self.table.paused = not self.table.paused
        elif key in ("m", "M"):
            self.table.muted = not self.table.muted
            self.table.save_score()
        elif key in ("Return", "KP_Enter") and self.table.over:
            self.table.reset()
        return True

    def release(self, _, event):
        key = Gdk.keyval_name(event.keyval)
        self.table.keys.discard(key)
        if key == "space":
            self.table.launch()
        return True

    def unfocus(self, *_):
        self.table.keys.clear()
        self.table.charge = 0
        if not self.table.over and any(not b.staged for b in self.table.balls):
            self.table.paused = True

    def close(self, *_):
        self.table.save_score()
        Gtk.main_quit()

    def tick(self):
        now = time.monotonic()
        self.accumulator += min(.05, now-self.clock)
        self.clock = now
        while self.accumulator >= STEP:
            self.table.advance()
            self.accumulator -= STEP
        if self.table.effects and not self.table.muted:
            self.sound.play(self.table.effects[-1])
        self.table.effects.clear()
        self.surface.queue_draw()
        return True

    def draw(self, widget, ctx):
        t = self.table
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        scale = min(width/820, height/770)
        ctx.set_source_rgb(.025, .026, .052)
        ctx.paint()
        ctx.translate((width-820*scale)/2, (height-770*scale)/2)
        ctx.scale(scale, scale)
        ctx.translate(12, 14)
        ctx.set_source_surface(self.art,0,0)
        ctx.paint()
        panel(ctx,548,12,252,720,(.04,.058,.10),(.19,.31,.41))
        for y in (156,224,292,360):
            panel(ctx,554,y,237,63,(.055,.084,.132),(.18,.28,.39),6)
        for path in (RAIL,RETURN):
            line(ctx,path,(.095,.14,.29),17)
            line(ctx,path,(.25,.43,.61),8)
            neon(ctx,path,CYAN,2)
        neon(ctx,SHOOTER_RAIL,(.35,.52,.89),2)
        neon(ctx,GATE,GOLD,2)
        for i,(ax,ay,bx,by,direction) in enumerate(SLINGS):
            hot=t.elapsed-t.hit.get(20+i,-10)<.15
            points=[(ax,ay),(bx,by),(ax-direction*13,by+12)]
            panel(ctx,min(ax,bx)-5,ay-8,abs(bx-ax)+11,11,(.08,.10,.18),(.22,.32,.43),3)
            for j in range(3):
                y=ay+15+j*12
                neon(ctx,[(ax+direction*j*8,y),(ax+direction*(j*8+13),y+7)],GOLD if hot else PINK,2)
            neon(ctx,points+[points[0]],GOLD if hot else PINK,2)
        panel(ctx,179,705,118,23,(.09,.055,.14),(.55,.19,.42),5)
        text(ctx,205,721,"BALL DRAIN",10,PINK,True)
        for i,x in enumerate(ROLLOVERS):
            panel(ctx,x-15,55,30,19,(.35,.23,.08) if i in t.rollovers else (.09,.18,.26),GOLD if i in t.rollovers else CYAN,5)
            text(ctx,x-4,69,"LINK"[i],11,GOLD if i in t.rollovers else CYAN,True)
        for x in (116, 342):
            line(ctx, [(x-34, 147),(x-28, 111),(x, 87),(x+29, 112),(x+34,147)], (.28,.17,.38), 10)
            neon(ctx, [(x-34,147),(x-28,111),(x,87),(x+29,112),(x+34,147)], PINK)
            for y in (112,123,134):
                line(ctx,[(x-9,y+4),(x,y-2),(x+9,y+4)],GOLD,1.3)
            text(ctx,x-29,163,"OVERCLOCK",8,PINK,True)
        for i, (x, y, r) in enumerate(BUMPERS):
            active = t.elapsed - t.hit.get(i, -10) < .15
            circle(ctx,x,y,r+10,PINK,.31 if active else .09)
            circle(ctx,x,y,r,PINK,.95)
            metal = cairo.RadialGradient(x-r*.24,y-r*.31,1,x,y,r-4)
            metal.add_color_stop_rgb(0,.42,.32,.57)
            metal.add_color_stop_rgb(.52,.19,.12,.31)
            metal.add_color_stop_rgb(1,.055,.025,.12)
            ctx.set_source(metal)
            ctx.arc(x,y,r-4,0,math.tau)
            ctx.fill()
            for angle in range(0,360,45):
                theta=math.radians(angle)
                circle(ctx,x+math.cos(theta)*(r-6),y+math.sin(theta)*(r-6),1.7,(.73,.80,.91))
            circle(ctx,x,y,r-12,CYAN,.9 if active else .3)
            text(ctx,x-9,y+5,f"0{i+1}",12,(.95,.94,1),True)
        for i,(x,y) in enumerate(TARGETS):
            color = GOLD if i in t.bank else CYAN
            circle(ctx,x,y,11,color,.95 if i in t.bank else .28)
            circle(ctx,x,y,5,color)
            text(ctx,x+13,y+4,f"D{i+1}",9,color,True)
        if self.table.elapsed < self.table.ball_save:
            text(ctx,182,552,"BALL SAVE",14,GOLD,True)
        for x,y,ex,ey in t.flippers():
            line(ctx,[(x,y),(ex,ey)],(.25,.09,.3),20)
            line(ctx,[(x,y),(ex,ey)],PINK,13)
            line(ctx,[(x,y),(ex,ey)],(1,.76,.9),3)
            circle(ctx,x,y,5,CYAN)
        for ball in t.balls:
            for i in range(5,0,-1):
                if not ball.staged:
                    circle(ctx,ball.x-ball.vx*i*.005,ball.y-ball.vy*i*.005,5,CYAN,(6-i)*.055)
            circle(ctx,ball.x,ball.y,13,CYAN,.19)
            shine = cairo.RadialGradient(ball.x-2.7,ball.y-3,0,ball.x,ball.y,RADIUS)
            shine.add_color_stop_rgb(0,1,1,1)
            shine.add_color_stop_rgb(.36,.72,.91,1)
            shine.add_color_stop_rgb(.71,.25,.46,.65)
            shine.add_color_stop_rgb(1,.09,.20,.33)
            ctx.set_source(shine)
            ctx.arc(ball.x,ball.y,RADIUS,0,math.tau)
            ctx.fill()
        ctx.set_source_rgb(*GOLD)
        ctx.rectangle(474,713,19*t.charge,5)
        ctx.fill()

        x = 554
        text(ctx,x,52,"SHADOW",38,CYAN,True)
        text(ctx,x,91,"PINBALL",38,(.94,.96,1),True)
        text(ctx,x,122,"TABLE 01  /  CIRCUIT BREACH",12,PINK,True)
        line(ctx,[(x,140),(x+239,140)],(.27,.31,.47))
        for y,label,value in ((180,"SCORE",f"{t.score:,}"),(248,"HIGH SCORE",f"{max(t.best,t.score):,}"),
                              (316,"BALLS LEFT",str(t.remaining)),(384,"MISSIONS",str(t.missions))):
            text(ctx,x,y,label,13,(.63,.72,.84),True)
            text(ctx,x,y+31,value,27,CYAN,True)
        text(ctx,x,445,f"x{t.multiplier} SCORE   /   {t.shots} RAMP SHOTS",12,PINK,True)
        text(ctx,x,467,f"DATA TARGETS  {len(t.bank)} / {len(TARGETS)}",13,GOLD,True)
        for i in range(len(TARGETS)):
            circle(ctx,x+6+i*22,484,5,GOLD,1 if i in t.bank else .22)
        text(ctx,x,529,"L SHIFT / R SHIFT",15,(.92,.93,1),True)
        text(ctx,x,550,"Left and right flippers",13,(.62,.72,.84))
        text(ctx,x,580,"SPACE",15,(.92,.93,1),True)
        text(ctx,x,601,"Hold, then release to launch",13,(.62,.72,.84))
        text(ctx,x,630,"P / ESC",15,(.92,.93,1),True)
        text(ctx,x,651,"Pause and resume",13,(.62,.72,.84))
        sound_status = "OFF" if t.muted else "ON" if self.sound.player else "UNAVAILABLE"
        text(ctx,x,675,"M  /  SOUND " + sound_status,12,(.62,.72,.84))
        message = "PAUSED" if t.paused else t.message
        text(ctx,x,706,message,9,GOLD if t.flash else CYAN,True)
        return False


if __name__ == "__main__":
    Pinball()
    Gtk.main()
