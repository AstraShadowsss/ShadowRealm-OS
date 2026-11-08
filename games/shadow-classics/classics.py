#!/usr/bin/python3
"""Six original, offline games for the ShadowRealm-OS arcade."""
from collections import deque
import math
import random
import sys

from arcade import Arcade, Gtk, Gdk, W, H, ICE, PINK, GOLD, WHITE, bg, dot, poly, rect, text

COLORS = (ICE, PINK, GOLD, (.45, .93, .42), (.63, .48, 1))
DIRECTIONS = (("left", "a", -1, 0), ("right", "d", 1, 0),
              ("up", "w", 0, -1), ("down", "s", 0, 1))


def direction(keys, default):
    return next(((x,y) for k,a,x,y in DIRECTIONS if keys & {k,a}),default)


class Classic:
    def reset(self):
        self.score = 0
        self.over = self.won = False
        self.effects = []

    def paint(self,c):
        bg(c,(.09,.045,.15))


class Coil(Classic):
    controls = "Arrows or WASD: Turn | M: Sound"
    hint = "Eat energy cells. Cross any edge to wrap around. Avoid your tail."
    nx,ny,cell=28,17,29
    ox,oy=44,101

    def __init__(self):self.reset()

    def reset(self):
        super().reset()
        self.body=deque([(8,8),(7,8),(6,8),(5,8)])
        self.heading=(1,0)
        self.timer=0
        self.place()

    def place(self):
        candidates=[(x,y) for x in range(self.nx) for y in range(self.ny) if (x,y) not in self.body]
        self.food=random.choice(candidates) if candidates else None
        if self.food is None:self.over=self.won=True

    def step(self,dt,keys):
        self.timer+=dt
        interval=max(.058,.16-self.score*.00042)
        if self.timer<interval:return
        self.timer-=interval
        dx,dy=direction(keys,self.heading)
        if (dx,dy)!=tuple(-v for v in self.heading):self.heading=dx,dy
        x,y=self.body[0]
        new=((x+self.heading[0])%self.nx,(y+self.heading[1])%self.ny)
        grow=new==self.food
        if new in (self.body if grow else list(self.body)[:-1]):
            self.over=True;self.effects.append("drain");return
        self.body.appendleft(new)
        if grow:
            self.score+=10;self.effects.append("target");self.place()
        else:self.body.pop()

    def draw(self,c):
        self.paint(c)
        text(c,44,88,f"LENGTH {len(self.body)}",15,GOLD)
        for y in range(self.ny):
            for x in range(self.nx):
                rect(c,self.ox+x*self.cell,self.oy+y*self.cell,self.cell-1,self.cell-1,
                     (.075,.10,.18) if (x+y)%2 else (.065,.087,.16))
        if self.food:
            x,y=self.food;x=self.ox+(x+.5)*self.cell;y=self.oy+(y+.5)*self.cell
            dot(c,x,y,14,PINK,.20);dot(c,x,y,8,PINK);dot(c,x-2,y-2,3,WHITE)
        for i,(x,y) in enumerate(self.body):
            x=self.ox+x*self.cell;y=self.oy+y*self.cell
            rect(c,x+2,y+2,self.cell-5,self.cell-5,ICE,max(.36,1-i*.045))
            if i==0:
                dx,dy=self.heading
                for side in (-1,1):
                    dot(c,x+14+dx*6+dy*side*6,y+14+dy*6-dx*side*6,3,(.02,.07,.12))


class Jump(Classic):
    controls = "Left/Right or A/D: Steer | M: Sound"
    hint = "Bounce up the rooftops. Gold launchpads send you higher."

    def __init__(self):self.reset()

    def reset(self):
        super().reset()
        self.x,self.y,self.vy,self.camera,self.t=450,520,-630,0,0
        self.platforms=[[450,555,148,False,False]]
        for i in range(1,9):self.generate(555-i*79,i)

    def generate(self,y,level):
        prev=self.platforms[-1][0]
        width=max(78,133-level*.35)
        x=min(W-width/2,max(width/2,prev+random.choice([-1,1])*random.randint(85,225)))
        self.platforms.append([x,y,width,level%7==0,level%5==0])

    def step(self,dt,keys):
        self.t+=dt
        dx,_=direction(keys,(0,0))
        self.x=(self.x+dx*365*dt)%W
        old=self.y
        self.vy+=1370*dt
        self.y+=self.vy*dt
        if self.vy>0:
            for x,y,w,boost,moving in self.platforms:
                if moving:x+=math.sin(self.t*1.8+y*.01)*38
                if old+18<=y<self.y+18 and abs(self.x-x)<w/2+12:
                    self.y=y-18;self.vy=-835 if boost else -575
                    self.effects.append("ramp" if boost else "bumper")
                    break
        self.camera=min(self.camera,self.y-272)
        self.score=max(self.score,int(-self.camera/6))
        while self.platforms[-1][1]>self.camera+65:
            self.generate(self.platforms[-1][1]-random.randint(68,93),int(-self.platforms[-1][1]/75))
        self.platforms=[p for p in self.platforms if p[1]<self.camera+H+64]
        if self.y-self.camera>H+45:self.over=True;self.effects.append("drain")

    def draw(self,c):
        self.paint(c)
        for i in range(18):
            x=(i*83)%W
            y=90+(i*127-self.camera*.34)%(H-60)
            rect(c,x,y,34+(i%4)*11,H-y,(.10,.13,.24),.62)
            for j in range(4):
                rect(c,x+7+(j%2)*14,y+13+(j//2)*22,5,8,PINK,.39)
        for x,y,w,boost,moving in self.platforms:
            if moving:x+=math.sin(self.t*1.8+y*.01)*38
            y-=self.camera;color=GOLD if boost else PINK if moving else ICE
            rect(c,x-w/2-4,y-4,w+8,20,color,.18)
            rect(c,x-w/2,y,w,12,(.14,.18,.32));rect(c,x-w/2,y,w,3,color)
        x,y=self.x,self.y-self.camera
        poly(c,[(x-16,y+10),(x-12,y-17),(x+12,y-17),(x+16,y+10),(x,y+18)],ICE)
        poly(c,[(x-13,y+8),(x-9,y-13),(x+9,y-13),(x+13,y+8),(x,y+14)],(.07,.13,.24))
        rect(c,x-8,y-7,16,4,GOLD)
        text(c,35,90,f"ALTITUDE {int(-self.camera)} M",15,GOLD)


class Brick(Classic):
    controls = "Left/Right or A/D: Paddle | Space: Launch | M: Sound"
    hint = "Aim with the paddle edges. Clear the grid to advance."

    def __init__(self):self.reset()

    def reset(self):
        super().reset()
        self.level,self.lives,self.px=1,3,450
        self.new_ball()
        self.build()

    def new_ball(self):
        self.x,self.y,self.vx,self.vy=self.px,558,0,0
        self.staged=True

    def build(self):
        self.bricks=[[70+i*86,131+j*35,j,2 if j==0 and self.level>1 else 1]
                     for j in range(5) for i in range(9)]

    def step(self,dt,keys):
        dx,_=direction(keys,(0,0))
        self.px=min(830,max(70,self.px+dx*630*dt))
        if self.staged:
            self.x=self.px
            if "space" in keys:
                self.staged=False;self.vx=160;self.vy=-390;self.effects.append("launch")
            return
        for _ in range(4):
            ox,oy=self.x,self.y
            self.x+=self.vx*dt/4;self.y+=self.vy*dt/4
            if self.x<21 or self.x>879:
                self.x=max(21,min(879,self.x));self.vx=-self.vx
            if self.y<82:self.y=82;self.vy=abs(self.vy)
            if self.vy>0 and oy<=571<=self.y and abs(self.x-self.px)<67:
                angle=(self.x-self.px)/67*1.05
                speed=min(750,math.hypot(self.vx,self.vy)+13)
                self.vx=math.sin(angle)*speed;self.vy=-math.cos(angle)*speed
                self.effects.append("bumper")
            for brick in self.bricks[:]:
                x,y,row,hp=brick
                if x-7<self.x<x+84 and y-7<self.y<y+33:
                    if oy<y-7 or oy>y+33:self.vy=-self.vy
                    else:self.vx=-self.vx
                    self.x,self.y=ox,oy
                    brick[3]-=1
                    if not brick[3]:
                        self.bricks.remove(brick);self.score+=50*(5-row)
                    self.effects.append("target");break
        if not self.bricks:
            self.level+=1;self.build();self.new_ball();self.effects.append("mission")
        elif self.y>H+8:
            self.lives-=1;self.effects.append("drain");self.new_ball()
            if not self.lives:self.over=True

    def draw(self,c):
        self.paint(c)
        for x in range(28,W,35):rect(c,x,110,1,H-110,ICE,.08)
        for x,y,row,hp in self.bricks:
            color=COLORS[row]
            rect(c,x-2,y-2,81,30,color,.15);rect(c,x,y,77,26,color,.82)
            rect(c,x+4,y+5,69,17,(.10,.10,.20),.63)
            if hp==2:rect(c,x+25,y+11,27,4,WHITE,.7)
        rect(c,self.px-65,577,130,12,ICE,.26);rect(c,self.px-61,572,122,10,ICE)
        dot(c,self.x,self.y,15,ICE,.22);dot(c,self.x,self.y,7,WHITE)
        text(c,31,95,f"LEVEL {self.level}   /   BALLS {self.lives}",15,GOLD)
        if self.staged:text(c,364,618,"SPACE TO SERVE",16,PINK)


MAZE = (
 "#####################",
 "#.........#.........#",
 "#.##.###..#..###.##.#",
 "#o##.###.....###.##o#",
 "#...................#",
 "###.#.##.###.##.#.###",
 "#...#....#.#....#...#",
 "#.#...##.....##...#.#",
 "#...#....#.#....#...#",
 "###.#.##.###.##.#.###",
 "#...................#",
 "#o##.###.....###.##o#",
 "#.##.###..#..###.##.#",
 "#.........#.........#",
 "#####################",
)


class Maze(Classic):
    controls = "Arrows or WASD: Move | M: Sound"
    hint = "Recover data nodes. Overclock cells disable sentinels."

    def __init__(self):self.reset()

    def reset(self):
        super().reset()
        self.level=1;self.lives=3;self.begin()

    def begin(self):
        self.food={(x,y):ch for y,row in enumerate(MAZE) for x,ch in enumerate(row) if ch in ".o"}
        self.positions()

    def positions(self):
        self.player=(10,7);self.previous_player=self.player;self.heading=(0,0);self.pending=(0,0)
        self.ghosts=[(9,4),(11,4),(9,10),(11,10)]
        self.previous_ghosts=self.ghosts[:]
        self.timer=self.ghost_timer=self.power=0
        self.invulnerable=3.2

    @staticmethod
    def open(p):
        x,y=p
        return 0<=y<len(MAZE) and 0<=x<len(MAZE[y]) and MAZE[y][x]!="#"

    def near(self,p):
        x,y=p
        return [(x+dx,y+dy) for _,__,dx,dy in DIRECTIONS if self.open((x+dx,y+dy))]

    def move(self,pos,i):
        if self.power>0 or random.random()<.18+.09*i:return random.choice(self.near(pos))
        q=deque([(pos,pos)]);seen={pos}
        while q:
            cell,first=q.popleft()
            if cell==self.player:return first
            for n in self.near(cell):
                if n not in seen:
                    seen.add(n);q.append((n,n if cell==pos else first))
        return pos

    def step(self,dt,keys):
        self.power=max(0,self.power-dt);self.invulnerable=max(0,self.invulnerable-dt)
        self.pending=direction(keys,self.pending)
        self.timer+=dt;self.ghost_timer+=dt
        if self.timer>=.12:
            self.timer-=.12
            self.previous_player=self.player
            x,y=self.player
            if self.open((x+self.pending[0],y+self.pending[1])):self.heading=self.pending
            n=(x+self.heading[0],y+self.heading[1])
            if self.open(n):self.player=n
            food=self.food.pop(self.player,None)
            if food=="o":self.power=7;self.score+=50;self.effects.append("ramp")
            elif food:self.score+=10
        self.collide()
        if self.ghost_timer>=max(.17,.35-self.level*.015):
            self.ghost_timer=0
            self.previous_ghosts=self.ghosts[:]
            self.ghosts=[self.move(g,i) for i,g in enumerate(self.ghosts)]
            self.collide()
        if not self.food:
            self.level+=1;self.begin();self.effects.append("mission")

    def collide(self):
        for i,g in enumerate(self.ghosts):
            if g!=self.player:continue
            if self.power>0:
                self.score+=200;self.ghosts[i]=(9+i%2*2,4 if i<2 else 10);self.effects.append("target")
            elif not self.invulnerable:
                self.lives-=1;self.effects.append("drain")
                if not self.lives:self.over=True
                else:self.positions()
                break

    def draw(self,c):
        self.paint(c)
        ox,oy,n=135,121,30
        text(c,135,100,f"MAZE {self.level}   /   LIVES {self.lives}",15,GOLD)
        for y,row in enumerate(MAZE):
            for x,ch in enumerate(row):
                px,py=ox+x*n,oy+y*n
                if ch=="#":
                    rect(c,px,py,n-1,n-1,(.105,.18,.32));rect(c,px+1,py+1,n-3,2,ICE,.34)
                elif (x,y) in self.food:poly(c,[(px+15,py+9),(px+21,py+15),(px+15,py+21),(px+9,py+15)],GOLD if ch=="o" else ICE,.9)
        def glide(old,new,amount):
            if math.dist(old,new)>1:return new
            return tuple(a+(b-a)*min(1,amount) for a,b in zip(old,new))
        for i,cell in enumerate(self.ghosts):
            x,y=glide(self.previous_ghosts[i],cell,self.ghost_timer/max(.17,.35-self.level*.015))
            x,y=ox+x*n+15,oy+y*n+15;color=ICE if self.power else COLORS[(i+1)%len(COLORS)]
            poly(c,[(x-12,y),(x-6,y-10),(x+6,y-10),(x+12,y),(x+6,y+10),(x-6,y+10)],color)
            dot(c,x-4,y-3,2,(.05,.08,.13));dot(c,x+4,y-3,2,(.05,.08,.13))
        x,y=glide(self.previous_player,self.player,self.timer/.12);x,y=ox+x*n+15,oy+y*n+15
        if self.invulnerable==0 or int(self.invulnerable*9)%2:
            c.save();c.translate(x,y)
            if self.heading!=(0,0):c.rotate(math.atan2(self.heading[1],self.heading[0]))
            dot(c,0,0,15,ICE,.17)
            poly(c,[(-11,-9),(13,0),(-11,9),(-5,0)],ICE)
            rect(c,-3,-2,7,4,WHITE)
            c.restore()
        if self.power:text(c,635,100,"POWER MODE",14,ICE)


SUITS=("S","H","C","D")
RANKS=("A","2","3","4","5","6","7","8","9","10","J","Q","K")
SYMBOLS=("\u2660","\u2665","\u2663","\u2666")
CW,CH=89,110


class Solitaire(Classic):
    controls = "Click stack then destination | U: Undo | H: Hint | N: New"
    hint = "Build eight same-suit runs from King down to Ace."
    suits = 1
    width, height = 76, 94
    top = 216

    def __init__(self):
        self.reset()

    def reset(self, seed=None):
        super().reset()
        self.seed = random.getrandbits(64) if seed is None else seed
        deck = [(rank, suit, False) for _ in range(8 // self.suits)
                for suit in range(self.suits) for rank in range(1, 14)]
        random.Random(self.seed).shuffle(deck)
        self.columns = []
        for i in range(10):
            pile = [deck.pop() for _ in range(6 if i < 4 else 5)]
            pile[-1] = (*pile[-1][:2], True)
            self.columns.append(pile)
        self.stock = deck
        self.completed, self.undo = [], []
        self.select, self.suggestion, self.key_latch = None, None, set()
        self.message = "Move descending suited stacks. Click STOCK to deal a row."

    def snapshot(self):
        self.undo.append(([pile[:] for pile in self.columns], self.stock[:],
                          self.completed[:], self.score))

    def step(self, dt, keys):
        fresh = keys - self.key_latch
        if "n" in fresh:
            self.reset()
        elif "r" in fresh:
            self.reset(self.seed)
        elif "u" in fresh and self.undo:
            self.columns, self.stock, self.completed, self.score = self.undo.pop()
            self.select = self.suggestion = None
            self.message = "Last action undone."
        elif "h" in fresh:
            self.hint_move()
        self.key_latch = set(keys)

    def movable(self, col, start):
        cards = self.columns[col][start:]
        return bool(cards and cards[0][2] and all(
            right[2] and left[0] == right[0] + 1 and left[1] == right[1]
            for left, right in zip(cards, cards[1:])))

    def fits(self, col, rank):
        pile = self.columns[col]
        return not pile or (pile[-1][2] and pile[-1][0] == rank + 1)

    def hint_move(self):
        self.suggestion = None
        choices = []
        for source, pile in enumerate(self.columns):
            for start, (rank, suit, _) in enumerate(pile):
                if not self.movable(source, start):
                    continue
                for target, dest in enumerate(self.columns):
                    if source == target or not self.fits(target, rank) or (not dest and start == 0):
                        continue
                    priority = (bool(dest and dest[-1][1] == suit), bool(start and not pile[start-1][2]), bool(dest))
                    choices.append((priority, source, start, target))
        if choices:
            _, source, start, target = max(choices)
            self.suggestion = (source, start, target)
            self.message = f"Hint: move the highlighted stack from column {source+1} to {target+1}."
        elif self.stock and all(self.columns):
            self.message = "Hint: deal a row from the stock."
        else:
            self.message = "No productive move found. Undo, replay this deal (R), or start a new deal (N)."

    def settle(self, col):
        pile = self.columns[col]
        while pile:
            if not pile[-1][2]:
                pile[-1] = (*pile[-1][:2], True)
            if len(pile) < 13 or pile[-13][0] != 13 or not self.movable(col, len(pile)-13):
                break
            self.completed.append(pile[-1][1])
            del pile[-13:]
            self.score += 500
            self.effects.append("ramp")
        if len(self.completed) == 8:
            self.over = self.won = True
            self.effects.append("mission")

    def move(self, source, start, dest):
        if source == dest or not self.movable(source, start) or not self.fits(dest, self.columns[source][start][0]):
            return False
        self.snapshot()
        self.columns[dest].extend(self.columns[source][start:])
        del self.columns[source][start:]
        self.settle(source)
        self.settle(dest)
        self.effects.append("target")
        return True

    def deal(self):
        if not self.stock:
            self.message = "The stock is empty."
            return
        if not all(self.columns):
            self.message = "Fill each empty column before dealing a row."
            return
        self.snapshot()
        for pile in self.columns:
            pile.append((*self.stock.pop()[:2], True))
        for col in range(10):
            self.settle(col)
        self.effects.append("bumper")
        self.message = "Stock row dealt."

    @staticmethod
    def colx(i):
        return 19 + i * 87

    def positions(self, pile):
        gaps = [24 if card[2] else 12 for card in pile[:-1]]
        scale = min(1, (588 - self.top - self.height) / max(1, sum(gaps)))
        ys = [self.top]
        for gap in gaps:
            ys.append(ys[-1] + gap * scale)
        return ys

    def click(self, x, y):
        self.suggestion = None
        if 79 <= y <= 107:
            for index, level in enumerate((1, 2, 4)):
                if 560 + 100*index <= x <= 648 + 100*index:
                    if level != self.suits:
                        self.suits = level
                        self.reset()
                    return
        if 18 <= x <= 111 and 115 <= y <= 190:
            self.select = None
            self.deal()
            return
        for dest, pile in enumerate(self.columns):
            left = self.colx(dest)
            ys = self.positions(pile)
            if not (left <= x <= left+self.width and self.top <= y <= ys[-1]+self.height):
                continue
            if self.select and self.move(*self.select, dest):
                self.select = None
                self.message = "Move complete."
                return
            index = max(i for i, top in enumerate(ys) if top <= y)
            choice = (dest, index)
            self.select = choice if self.movable(*choice) and self.select != choice else None
            self.message = "Select a destination column." if self.select else "Select a face-up suited stack."
            return
        self.select = None

    def card(self, c, x, y, value, label="", highlight=False):
        border = GOLD if highlight else (.22,.48,.64)
        rect(c,x-1,y-1,self.width+2,self.height+2,border)
        if value is None:
            rect(c,x,y,self.width,self.height,(.035,.08,.16))
            if label:
                text(c,x+9,y+34,label,12,ICE)
            return
        rank,suit,face = value
        if not face:
            rect(c,x,y,self.width,self.height,(.09,.08,.23))
            poly(c,[(x+38,y+9),(x+65,y+45),(x+38,y+82),(x+11,y+45)],(.36,.19,.59))
            poly(c,[(x+38,y+20),(x+55,y+45),(x+38,y+69),(x+21,y+45)],(.11,.23,.39))
            return
        rect(c,x,y,self.width,self.height,(.045,.08,.16))
        ink = (ICE,PINK,GOLD,(.62,.62,1))[suit]
        text(c,x+6,y+18,RANKS[rank-1]+SYMBOLS[suit],17,ink)
        text(c,x+23,y+65,SYMBOLS[suit],31,ink)

    def draw(self,c):
        self.paint(c)
        text(c,19,101,"SPIDER PROTOCOL   /   K → A",18,ICE)
        for i,level in enumerate((1,2,4)):
            x=560+100*i
            rect(c,x,79,88,28,(.15,.26,.36) if self.suits==level else (.07,.11,.21))
            text(c,x+10,98,f"{level} SUIT" if level==1 else f"{level} SUITS",13,GOLD if self.suits==level else ICE)
        rect(c,18,115,93,75,(.12,.09,.25))
        text(c,28,144,"STOCK",15,ICE)
        text(c,28,170,f"{len(self.stock)//10} ROWS",13,GOLD)
        text(c,137,140,"COMPLETED RUNS",14,ICE)
        for i in range(8):
            x=139+i*42
            rect(c,x,151,34,30,(.14,.29,.34) if i<len(self.completed) else (.055,.12,.20))
            if i<len(self.completed):
                text(c,x+8,173,SYMBOLS[self.completed[i]],18,GOLD)
        text(c,515,164,"U Undo   H Hint   R Replay   N New",14,ICE)
        for col,pile in enumerate(self.columns):
            x=self.colx(col)
            target=self.suggestion and self.suggestion[2]==col
            text(c,x+4,208,f"{col+1:02d}",13,GOLD if target else ICE)
            if not pile:
                self.card(c,x,self.top,None,"EMPTY",target)
            for i,(y,card) in enumerate(zip(self.positions(pile),pile)):
                selected=self.select and self.select[0]==col and i>=self.select[1]
                hinted=self.suggestion and self.suggestion[:2]==(col,i)
                self.card(c,x,y,card,highlight=bool(selected or hinted or (target and i==len(pile)-1)))
        text(c,19,616,self.message,15,GOLD)


# An elliptical spiral with continuously changing curvature and open sight lines.
PATH = []
for i in range(241):
    t = i / 240
    angle = math.pi * (1.11 + 3.08*t)
    PATH.append((450 + (396-265*t)*math.cos(angle), 346 + (229-138*t)*math.sin(angle)))
PATH_LEN = [0.0]
for a, b in zip(PATH, PATH[1:]):
    PATH_LEN.append(PATH_LEN[-1] + math.dist(a, b))


def path_at(distance):
    from bisect import bisect_left
    s = max(0, min(PATH_LEN[-1], distance))
    i = max(1, bisect_left(PATH_LEN, s))
    a, b = PATH[i-1:i+1]
    f = (s-PATH_LEN[i-1]) / (PATH_LEN[i]-PATH_LEN[i-1])
    return a[0]+f*(b[0]-a[0]), a[1]+f*(b[1]-a[1])


class Marble(Classic):
    controls = "Mouse: Aim | Click: Shoot | Space: Swap | M: Sound"
    hint = "Match three or more. Stop the chain before it reaches the exit."
    gun=(450,337)
    spacing=27

    def __init__(self):self.reset()

    def reset(self):
        super().reset()
        self.round=0;self.aim=(450,185);self.keys=set();self.new_round()

    def new_round(self):
        self.round+=1
        colors=[]
        while len(colors)<min(43,25+self.round*3):
            colors.extend([random.randrange(len(COLORS))]*random.choice((1,2,2)))
        self.chain=colors
        self.head=550
        self.shot=None
        self.pick()

    def pick(self):
        choices=list(set(self.chain)) or list(range(len(COLORS)))
        self.current=random.choice(choices);self.next=random.choice(choices)

    def motion(self,x,y):self.aim=(x,y)

    def click(self,x,y):
        if self.shot:return
        gx,gy=self.gun
        length=math.hypot(x-gx,y-gy)
        if length<5:return
        self.shot=[gx,gy,(x-gx)/length*650,(y-gy)/length*650,self.current]
        self.current=self.next if self.next in self.chain else random.choice(self.chain)
        self.next=random.choice(self.chain) if self.chain else random.randrange(len(COLORS))
        self.effects.append("launch")

    def hit(self,index,color):
        self.chain.insert(index,color);self.head+=self.spacing
        combo=1
        while self.chain and 0<=index<len(self.chain):
            color=self.chain[index];a=b=index
            while a>0 and self.chain[a-1]==color:a-=1
            while b+1<len(self.chain) and self.chain[b+1]==color:b+=1
            if b-a<2:break
            count=b-a+1;del self.chain[a:b+1];self.head-=self.spacing*count
            self.score+=count*100*combo;combo+=1;self.effects.append("target")
            if a==0 or a==len(self.chain) or self.chain[a-1]!=self.chain[a]:break
            index=a
        if not self.chain:
            self.score+=1000;self.effects.append("mission")
            if self.round == 5:
                self.over = self.won = True
            else:
                self.new_round()
        elif self.current not in self.chain or self.next not in self.chain:
            self.current = self.current if self.current in self.chain else random.choice(self.chain)
            self.next = self.next if self.next in self.chain else random.choice(self.chain)

    def step(self,dt,keys):
        if "space" in keys and "space" not in self.keys:
            self.current,self.next=self.next,self.current
        self.keys=set(keys)
        self.head+=(36+self.round*9)*dt
        if self.head>=PATH_LEN[-1]:
            self.over=True;self.effects.append("drain");return
        if not self.shot:return
        x,y,vx,vy,color=self.shot
        for _ in range(3):
            x+=vx*dt/3;y+=vy*dt/3
            self.shot[0:2]=[x,y]
            for i in range(len(self.chain)):
                s=self.head-i*self.spacing
                if s<0:break
                px,py=path_at(s)
                if math.hypot(x-px,y-py)<22:
                    tx,ty=path_at(s+3)
                    index=i if (x-px)*(tx-px)+(y-py)*(ty-py)>0 else i+1
                    self.shot=None;self.hit(index,color);return
        if not (0<x<W and 60<y<H):self.shot=None

    def marble(self,c,x,y,r,color):
        col=COLORS[color]
        dot(c,x,y,r+4,col,.19);dot(c,x,y,r,col);dot(c,x,y,r-3,col,.8);dot(c,x-3,y-4,3,WHITE,.83)

    def draw(self,c):
        self.paint(c)
        for width,col in ((38,(.13,.12,.27)),(30,(.075,.10,.21)),(2,(.28,.38,.61))):
            c.set_line_cap(1);c.set_line_join(1);c.set_line_width(width);c.set_source_rgb(*col)
            c.move_to(*PATH[0])
            for point in PATH[1:]:c.line_to(*point)
            c.stroke()
        end=PATH[-1];dot(c,*end,23,PINK,.62);dot(c,*end,14,(.06,.025,.10))
        for i,color in enumerate(self.chain):
            s=self.head-i*self.spacing
            if s<0:break
            self.marble(c,*path_at(s),11,color)
        x,y=self.gun;a=math.atan2(self.aim[1]-y,self.aim[0]-x)
        dot(c,x,y,26,ICE,.15);dot(c,x,y,22,(.18,.24,.43))
        for i in range(2,7):dot(c,x+math.cos(a)*i*14,y+math.sin(a)*i*14,2,ICE,.6)
        self.marble(c,x,y,12,self.current)
        self.marble(c,x,y+31,7,self.next)
        if self.shot:self.marble(c,*self.shot[:2],10,self.shot[-1])
        text(c,35,101,f"STAGE {self.round}/5   /   {len(self.chain)} MARBLES",15,GOLD)


class ClassicWindow(Arcade):
    def __init__(self,name,identity,model):
        super().__init__(name,identity,model)
        self.drag_origin = None
        self.drawing.add_events(Gdk.EventMask.BUTTON_PRESS_MASK|Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.POINTER_MOTION_MASK)
        self.drawing.connect("button-press-event",self.click)
        self.drawing.connect("button-release-event",self.release_click)
        self.drawing.connect("motion-notify-event",self.motion)

    def coords(self,e):
        w,h=self.drawing.get_allocated_width(),self.drawing.get_allocated_height()
        scale=min(w/W,h/H)
        return (e.x-(w-W*scale)/2)/scale,(e.y-(h-H*scale)/2)/scale

    def click(self,_,e):
        self.drag_origin = None
        if e.button==1 and self.started and not self.paused and not self.model.over and hasattr(self.model,"click"):
            point = self.coords(e)
            self.model.click(*point)
            if isinstance(self.model, Solitaire) and self.model.select:
                self.drag_origin = point
        return True

    def release_click(self,_,e):
        origin, self.drag_origin = self.drag_origin, None
        if e.button == 1 and origin and not self.paused and not self.model.over:
            point = self.coords(e)
            if math.dist(origin,point) > 12:
                self.model.click(*point)
        return True

    def motion(self,_,e):
        if hasattr(self.model,"motion"):self.model.motion(*self.coords(e))
        return True

    def draw(self,widget,c):
        result=super().draw(widget,c)
        if self.model.won:
            w,h=widget.get_allocated_width(),widget.get_allocated_height()
            scale=min(w/W,h/H)
            c.save()
            c.identity_matrix()
            c.translate((w-W*scale)/2,(h-H*scale)/2);c.scale(scale,scale)
            rect(c,205,228,490,62,(.045,.07,.14))
            text(c,211,260,"YOU WIN",34,GOLD)
            c.restore()
        return result


GAMES={
    "neon-ascent":("Neon Ascent",Jump),
    "circuit-chase":("Circuit Chase",Maze),
    "shadow-snake":("Shadow Snake",Coil),
    "shadow-solitaire":("Shadow Spider Solitaire",Solitaire),
    "neon-breaker":("Neon Breaker",Brick),
    "marble-reactor":("Marble Reactor",Marble),
}


if __name__=="__main__":
    identity=sys.argv[1]
    title,model=GAMES[identity]
    ClassicWindow(title,identity,model())
    Gtk.main()
