#!/usr/bin/python3
"""Offline arcade games for ShadowRealm-OS."""
import cairo
import json
import math
import os
import random
import runpy
import sys
import time
from pathlib import Path

if os.name == "nt":
    from windows_game_ui import Gtk, Gdk, GLib
else:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk, GLib

W, H = 900, 640
ICE = (.31, .93, 1)
PINK = (1, .25, .66)
GOLD = (1, .76, .36)
WHITE = (.87, .94, 1)


def rect(c, x, y, w, h, color, alpha=1):
    c.set_source_rgba(*color, alpha)
    c.rectangle(x, y, w, h)
    c.fill()


def poly(c, points, color, alpha=1):
    c.set_source_rgba(*color, alpha)
    c.move_to(*points[0])
    for point in points[1:]:
        c.line_to(*point)
    c.close_path()
    c.fill()


def dot(c, x, y, r, color, alpha=1):
    c.set_source_rgba(*color, alpha)
    c.arc(x, y, r, 0, math.tau)
    c.fill()


def text(c, x, y, label, size=16, color=WHITE):
    c.set_source_rgb(*color)
    c.select_font_face("Sans", 0, 1)
    c.set_font_size(size)
    c.move_to(x, y)
    c.show_text(label)


def bg(c, bottom):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, .025, .028, .083)
    g.add_color_stop_rgb(1, *bottom)
    c.set_source(g)
    c.paint()


class Arcade(Gtk.Window):
    def __init__(self, name, identity, model):
        super().__init__(title=name)
        self.name, self.identity, self.model = name, identity, model
        self.set_icon_name(identity)
        self.set_default_size(900, 640)
        self.set_size_request(550, 395)
        home = Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))
        self.save_path = home/identity/"settings.json"
        try:
            state = json.loads(self.save_path.read_text())
        except (OSError, ValueError):
            state = {}
        self.best = state.get("best", 0) if isinstance(state, dict) else 0
        self.best = max(0,self.best) if isinstance(self.best,int) else 0
        self.mute = isinstance(state,dict) and state.get("mute") is True
        audio_path = Path(__file__).resolve().with_name("arcade-sound.py")
        self.audio = runpy.run_path(str(audio_path), run_name="shadow_arcade_sound")["Sound"]()
        self.keys, self.clock = set(), time.monotonic()
        self.started = self.paused = False
        self.drawing = Gtk.DrawingArea()
        self.add(self.drawing)
        self.drawing.connect("draw", self.draw)
        self.connect("key-press-event", self.press)
        self.connect("key-release-event", self.release)
        self.connect("focus-out-event", self.focus_out)
        self.connect("destroy", self.close)
        GLib.timeout_add(16, self.tick)
        self.show_all()

    def save(self):
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.save_path.with_suffix(".new")
            tmp.write_text(json.dumps({"best":max(self.best,int(self.model.score)), "mute":self.mute}))
            tmp.replace(self.save_path)
        except OSError:
            pass

    def close(self, *_):
        self.save()
        Gtk.main_quit()

    def focus_out(self, *_):
        self.keys.clear()
        if self.started and not self.model.over:
            self.paused = True

    def press(self, _, event):
        key = Gdk.keyval_name(event.keyval).lower()
        if key not in self.keys:
            if key in ("escape", "p") and self.started:
                self.paused = not self.paused
            elif key == "m":
                self.mute = not self.mute
                self.save()
            elif key == "return" and (not self.started or self.model.over):
                self.best = max(self.best, int(self.model.score))
                self.model.reset()
                self.started, self.paused = True, False
                self.audio.play("launch") if not self.mute else None
        self.keys.add(key)
        return True

    def release(self, _, event):
        self.keys.discard(Gdk.keyval_name(event.keyval).lower())
        return True

    def tick(self):
        now = time.monotonic()
        dt, self.clock = min(.04, now-self.clock), now
        if self.started and not self.paused and not self.model.over:
            self.model.step(dt, self.keys)
            if self.model.effects and not self.mute:
                self.audio.play(self.model.effects[-1])
            self.model.effects.clear()
            if self.model.over:
                self.save()
        self.drawing.queue_draw()
        return True

    def draw(self, widget, c):
        w, h = widget.get_allocated_width(), widget.get_allocated_height()
        s = min(w/W, h/H)
        c.set_source_rgb(.018,.023,.045)
        c.paint()
        c.translate((w-W*s)/2,(h-H*s)/2)
        c.scale(s,s)
        c.rectangle(0,0,W,H)
        c.clip()
        self.model.draw(c)
        rect(c,0,0,W,60,(.025,.04,.08),.93)
        text(c,25,37,self.name.upper(),24,ICE)
        text(c,375,36,f"SCORE  {int(self.model.score):,}",17,WHITE)
        text(c,610,36,f"BEST  {max(self.best,int(self.model.score)):,}",17,GOLD)
        text(c,804,36,"MUTE" if self.mute else "AUDIO",12,PINK)
        if not self.started or self.paused or self.model.over:
            rect(c,0,61,W,H-61,(.017,.022,.054),.76)
            rect(c,180,209,540,230,(.045,.07,.14))
            rect(c,180,209,540,3,ICE)
            text(c,211,260,"SIGNAL LOST" if self.model.over else "PAUSED" if self.paused else self.name.upper(),34,ICE)
            text(c,211,302,self.model.controls,15)
            text(c,211,340,self.model.hint,14,GOLD)
            text(c,211,395,"P / ESC TO RESUME" if self.paused and not self.model.over else "ENTER TO PLAY",18,PINK)
        return False


class Invaders:
    controls = "Arrows or A/D: Move | Space: Fire | M: Sound"
    hint = "Drones dive out of formation. Catch cyan upgrades."
    def __init__(self):
        self.stars = [(random.randrange(W),random.randrange(H),random.uniform(.4,2.3)) for _ in range(100)]
        self.reset()

    def reset(self):
        self.x, self.t, self.score, self.hp, self.wave = 450,0,0,3,0
        self.effects, self.shots, self.bolts, self.drops, self.sparks = [],[],[],[],[]
        self.fire = self.power = self.protect = 0
        self.over = False
        self.spawn()

    def spawn(self):
        self.wave += 1
        self.dive_at = self.t+2
        if self.wave % 4 == 0:
            self.foes = [[450,155,0,0,16+self.wave,False,True]]
        else:
            self.foes = [[160+col*77,124+row*57,col,row,1+(row==0 and self.wave>1),False,False]
                         for row in range(3) for col in range(8)]

    def burst(self,x,y,color):
        for _ in range(9):
            self.sparks.append([x,y,random.uniform(-125,125),random.uniform(-130,130),.44,color])

    def step(self, dt, keys):
        self.t += dt
        self.x = max(31,min(W-31,self.x+430*dt*(bool(keys&{"right","d"})-bool(keys&{"left","a"}))))
        if "space" in keys and self.t>=self.fire:
            self.fire=self.t+(.11 if self.power>self.t else .24)
            self.shots.append([self.x,555])
            if self.power>self.t:self.shots.extend(([self.x-17,562],[self.x+17,562]))
            self.effects.append("bumper")
        if self.t>=self.dive_at and self.foes:
            self.dive_at=self.t+max(.43,1.7-self.wave*.095)
            foe=random.choice(self.foes)
            if foe[-1] or random.random()<.44:
                self.bolts.extend([foe[0]+offset,foe[1]+10] for offset in ((-44,0,44) if foe[-1] else (0,)))
            else:
                foe[5]=True
        for foe in self.foes:
            if foe[-1]:
                foe[0]=450+math.sin(self.t*1.4)*265
            elif foe[5]:
                foe[0]+=(self.x-foe[0])*dt*.7
                foe[1]+=dt*(195+13*self.wave)
                if foe[1]>H+20:foe[5]=False
            else:
                foe[0]=167+foe[2]*78+math.sin(self.t*(1.1+self.wave*.1))*67
                foe[1]=128+foe[3]*57+math.sin(self.t*2.1+foe[2]*.54)*15
        for shot in self.shots[:]:
            shot[1]-=590*dt
            if shot[1]<65:self.shots.remove(shot);continue
            for foe in self.foes[:]:
                if abs(shot[0]-foe[0])<(66 if foe[-1] else 22) and abs(shot[1]-foe[1])<23:
                    self.shots.remove(shot)
                    foe[4]-=1
                    if foe[4]<=0:
                        self.foes.remove(foe)
                        self.score+=1200 if foe[-1] else 125*self.wave
                        self.burst(foe[0],foe[1],PINK)
                        if foe[-1] or random.random()<.13:self.drops.append([foe[0],foe[1]])
                        self.effects.append("mission" if foe[-1] else "target")
                    break
        for bolt in self.bolts[:]:
            bolt[1]+=(260+self.wave*12)*dt
            if bolt[1]>H:self.bolts.remove(bolt)
            elif abs(bolt[0]-self.x)<25 and abs(bolt[1]-579)<20:
                self.bolts.remove(bolt)
                self.damage()
        for foe in self.foes:
            if foe[5] and abs(foe[0]-self.x)<31 and abs(foe[1]-579)<25:self.damage()
        for drop in self.drops[:]:
            drop[1]+=125*dt
            if drop[1]>H:self.drops.remove(drop)
            elif abs(drop[0]-self.x)<37 and abs(drop[1]-579)<25:
                self.drops.remove(drop)
                self.power=self.t+8
                self.effects.append("ramp")
        for spark in self.sparks[:]:
            spark[0]+=spark[2]*dt;spark[1]+=spark[3]*dt;spark[4]-=dt
            if spark[4]<=0:self.sparks.remove(spark)
        if not self.foes:self.spawn()

    def damage(self):
        if self.t<self.protect:return
        self.hp-=1;self.protect=self.t+1.5
        self.effects.append("drain")
        self.burst(self.x,579,ICE)
        self.over=self.hp<=0

    def draw(self,c):
        bg(c,(.12,.047,.17))
        for x,y,z in self.stars:dot(c,x,(y+self.t*15*z)%H,z,ICE,.15+z*.18)
        for foe in self.foes:
            x,y=foe[:2];s=2.5 if foe[-1] else 1
            c.save();c.translate(x,y);c.scale(s,s)
            dot(c,0,0,25,PINK,.12)
            poly(c,[(-21,-11),(-11,-19),(11,-19),(21,-11),(18,9),(9,11),(8,18),(-8,18),(-9,11),(-18,9)],PINK)
            poly(c,[(-17,-9),(-9,-15),(9,-15),(17,-9),(15,6),(7,8),(5,14),(-5,14),(-7,8),(-15,6)],(.17,.1,.25))
            dot(c,-8,-3,4,ICE);dot(c,8,-3,4,ICE)
            rect(c,-2,3,4,4,GOLD)
            c.restore()
        for x,y in self.shots:rect(c,x-2,y-9,4,18,ICE)
        for x,y in self.bolts:dot(c,x,y,5,PINK)
        for x,y in self.drops:
            dot(c,x,y,14,ICE,.18);poly(c,[(x,y-9),(x+9,y),(x,y+9),(x-9,y)],ICE)
        for x,y,_,__,a,color in self.sparks:dot(c,x,y,3,color,a/.44)
        if self.t>=self.protect or int(self.t*13)%2:
            x=self.x
            poly(c,[(x-25,594),(x-13,568),(x,551),(x+13,568),(x+25,594),(x,587)],ICE)
            poly(c,[(x-15,589),(x,558),(x+15,589),(x,583)],(.15,.27,.48))
            dot(c,x,578,5,GOLD)
            poly(c,[(x-7,589),(x+7,589),(x,614+5*math.sin(self.t*35))],PINK)
        text(c,26,88,f"WAVE {self.wave:02}   /   HULL {self.hp}",15,GOLD)
        if self.power>self.t:text(c,625,88,"TRIPLE SHOT ACTIVE",14,ICE)


class Runner:
    controls = "Space or Up: Jump | Down or Shift: Slide | M: Sound"
    hint = "Jump firewalls. Slide under drones. Collect shield cells."
    def __init__(self):
        rng=random.Random(31)
        self.city=[[(rng.randint(32,96),rng.randint(90,300)) for _ in range(25)] for _ in range(3)]
        self.reset()

    def reset(self):
        self.y,self.v,self.t,self.score,self.hp=503,0,0,0,3
        self.obstacles,self.cells,self.effects=[],[],[]
        self.next,self.shield,self.invulnerable=1.3,0,0
        self.over=self.sliding=False
        self.jump_was_down=False
        self.distance=0
        self.streak=0

    def step(self,dt,keys):
        self.t+=dt
        speed=min(740,290+self.t*7)
        self.distance+=speed*dt
        self.score+=dt*(speed/8)
        jump=bool(keys&{"space","up","w"})
        grounded=self.y>=503
        self.sliding=grounded and bool(keys&{"down","s","shift_l","shift_r"})
        if jump and not self.jump_was_down and grounded and not self.sliding:
            self.v=-665;self.effects.append("launch")
        self.jump_was_down=jump
        self.v+=1640*dt
        self.y=min(503,self.y+self.v*dt)
        if self.y>=503:self.v=0
        if self.t>=self.next:
            self.next=self.t+max(.87,1.64-self.t*.012)+random.random()*.36
            kind=random.choice(("firewall","firewall","drone"))
            self.obstacles.append([W+55,kind,False])
            if random.random()<.56:
                self.cells.append([W+165,395 if kind=="firewall" else 481,random.random()<.2])
        for obstacle in self.obstacles[:]:
            obstacle[0]-=speed*dt
            x,kind,done=obstacle
            if x<-60:self.obstacles.remove(obstacle);continue
            top,bottom=(451,505) if kind=="firewall" else (397,458)
            height=30 if self.sliding else 70
            if not done and x<213 and x+46>165 and self.y>top and self.y-height<bottom:
                obstacle[2]=True
                if self.t>=self.invulnerable:
                    if self.t<self.shield:self.shield=0
                    else:self.hp-=1
                    self.streak=0;self.invulnerable=self.t+1.4
                    self.effects.append("drain")
                    self.over=self.hp<=0
            elif not done and x+46<165:
                obstacle[2]=True;self.streak+=1;self.score+=50+min(100,self.streak*5)
        for cell in self.cells[:]:
            cell[0]-=speed*dt
            x,y,shield=cell
            if x<-25:self.cells.remove(cell)
            elif abs(x-188)<34 and self.y-75<y<self.y+12:
                self.cells.remove(cell)
                if shield:self.shield=self.t+12
                self.score+=275 if shield else 140
                self.effects.append("ramp" if shield else "target")

    def draw(self,c):
        bg(c,(.20,.049,.19))
        dot(c,650,217,75,PINK,.16);dot(c,650,217,61,PINK,.39)
        for layer,blocks in enumerate(self.city):
            speed=(.06,.14,.30)[layer]
            total=sum(w+9 for w,_ in blocks)
            x=-(self.distance*speed)%total-total
            for w,h in blocks*3:
                base=468+layer*15
                if -w<=x<=W:
                    top=base-h*(.55+layer*.17)
                    rect(c,x,top,w,base-top,(.042+layer*.018,.075+layer*.01,.15+layer*.021))
                    rect(c,x,top,w,2,(.25,.29,.49),.5)
                    for dx in range(8,w-5,13):
                        for y in range(int(top)+12,base-8,19):
                            if (dx+y)%7<3:rect(c,x+dx,y,4,7,ICE if layer!=1 else PINK,.30+layer*.10)
                x+=w+9
        rect(c,0,504,W,136,(.04,.052,.1))
        rect(c,0,503,W,4,ICE,.87)
        for i in range(-1,13):
            x=(i*84-self.distance)%1008
            poly(c,[(x,554),(x+43,554),(x+31,560),(x-8,560)],(.18,.30,.47))
        for x,kind,_ in self.obstacles:
            if kind=="firewall":
                rect(c,x-6,447,56,62,PINK,.14)
                rect(c,x,454,45,49,(.30,.10,.28))
                for i in range(5):rect(c,x+5+i*8,456,3,45,PINK,.75)
                rect(c,x,454,45,4,GOLD)
            else:
                dot(c,x+23,427,35,PINK,.12)
                poly(c,[(x-10,418),(x+9,405),(x+38,405),(x+56,418),(x+41,449),(x+6,449)],(.23,.13,.36))
                rect(c,x,422,46,4,PINK)
                dot(c,x+23,429,7,GOLD)
        for x,y,shield in self.cells:
            color=ICE if shield else GOLD
            dot(c,x,y,17,color,.16)
            poly(c,[(x,y-11),(x+10,y),(x,y+11),(x-10,y)],color)
        if self.t>=self.invulnerable or int(self.t*13)%2:
            x,y=188,self.y
            if self.t<self.shield:dot(c,x,y-36,48,ICE,.18)
            ink=(.024,.022,.056)
            rim=(.37,.38,.62)
            if self.sliding:
                body=[(x-39,y-8),(x-9,y-17),(x+6,y-30),(x+24,y-28),
                      (x+36,y-16),(x+23,y-5),(x-17,y-4)]
                poly(c,body,rim)
                poly(c,[(x-35,y-8),(x-8,y-15),(x+8,y-28),(x+22,y-26),
                        (x+33,y-16),(x+21,y-7),(x-15,y-6)],ink)
                dot(c,x+22,y-19,1.8,ICE)
            else:
                stride=12*math.sin(self.t*23)
                cape=[(x-3,y-62),(x-20,y-58),(x-39,y-33),(x-48,y-20),
                      (x-19,y-24),(x+8,y-31),(x+18,y-46)]
                poly(c,cape,rim)
                poly(c,[(x-4,y-59),(x-19,y-56),(x-37,y-33),(x-44,y-22),
                        (x-18,y-27),(x+7,y-33),(x+15,y-46)],ink)
                for dx,knee in ((-8,stride),(10,-stride)):
                    poly(c,[(x+dx-6,y-30),(x+dx+7,y-29),(x+knee+dx+8,y-4),
                            (x+knee+dx-3,y-2)],rim)
                    poly(c,[(x+dx-4,y-29),(x+dx+5,y-28),(x+knee+dx+5,y-6),
                            (x+knee+dx-2,y-5)],ink)
                dot(c,x+5,y-60,14,rim)
                dot(c,x+5,y-60,12,ink)
                poly(c,[(x-5,y-66),(x+2,y-73),(x+14,y-68),(x+16,y-57),(x+5,y-53)],ink)
                rect(c,x+9,y-62,7,2,ICE)
        text(c,26,88,f"ARMOR {self.hp}   /   {int(self.distance/10)} M",15,GOLD)
        text(c,662,88,f"STREAK {self.streak:02}",15,ICE)
        if self.t<self.shield:text(c,26,112,"SHIELD ACTIVE",13,ICE)


if __name__ == "__main__":
    identity = sys.argv[1]
    title, model = {"skull-invaders":("Skull Invaders",Invaders),
                    "shadow-runner":("Shadow Runner",Runner)}[identity]
    Arcade(title,identity,model())
    Gtk.main()
