import math,random
from arcade import Invaders
from classics import Maze

maze=Maze();seen={maze.player};pending=[maze.player]
while pending:
    for point in maze.near(pending.pop()):
        if point not in seen:seen.add(point);pending.append(point)
assert set(maze.food)<=seen,'Unreachable required data node'
for x,y,direction in [(824,463,(0,-1)),(782,505,(-1,0)),(866,505,(1,0)),(824,547,(0,1))]:
    maze.click(x,y);assert maze.pending==direction
maze.swipe(80,10);assert maze.pending==(1,0)
maze.swipe(5,-90);assert maze.pending==(0,-1)

for kind,count in [('double',2),('triple',3),('shield',1),('repair',1)]:
    game=Invaders();game.hp=2;game.drops=[[game.x,579,kind]]
    game.step(.001,set());game.step(.01,{'space'})
    assert len(game.shots)==count,(kind,len(game.shots))
    if kind=='shield':
        hp=game.hp;game.damage();assert game.hp==hp
        game.t=game.shield_until+1;game.protect=0;game.damage();assert game.hp==hp-1
    if kind=='repair':assert game.hp==3

game=Invaders();bosses=[]
for wave in range(1,13):
    assert game.wave==wave
    if wave%4==0:
        boss=game.foes[0];bosses.append(game.enemy_kind(boss))
        assert boss[4]==game.boss_health_max
        game.enemy_fire(boss);assert all(len(b)==4 for b in game.bolts)
    game.spawn()
assert bosses==[0,1,2]
for seed in range(12):
    random.seed(seed);game=Invaders()
    for frame in range(1800):
        game.protect=game.t+1
        game.step(1/60,{'space','right' if frame//120%2 else 'left'})
        assert all(math.isfinite(v) for foe in game.foes for v in foe[:5])
        assert len(game.shots)<100 and len(game.bolts)<300
print('PASS reachable Circuit Chase map, direction controls, weapon/shield/repair behavior, three boss types and 12 seeded simulations')
