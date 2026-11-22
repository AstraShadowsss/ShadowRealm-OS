import collections, math, random
from classics import Solitaire, Marble, PATH, PATH_LEN, path_at, MARBLE_TRACKS, marble_path
for suits in (1,2,4):
    for seed in range(20):
        g=Solitaire(); g.suits=suits; g.reset(seed)
        assert list(map(len,g.columns))==[6]*4+[5]*6 and len(g.stock)==50
        counts=collections.Counter((r,s) for pile in [*g.columns,g.stock] for r,s,_ in pile)
        rng=random.Random(seed)
        for _ in range(120):
            moves=[(i,j,k) for i,p in enumerate(g.columns) for j,c in enumerate(p)
                   if g.movable(i,j) for k in range(10) if i!=k and g.fits(k,c[0])]
            if g.stock and all(g.columns) and (not moves or rng.random()<.15): g.deal()
            elif moves: assert g.move(*rng.choice(moves))
            elif g.undo: g.step(0,set()); g.step(0,{'u'})
            else: break
            actual=collections.Counter((r,s) for pile in [*g.columns,g.stock] for r,s,_ in pile)
            actual.update((r,s) for s in g.completed for r in range(1,14))
            assert counts==actual and len(g.stock)%10==0
            assert all(not p or p[-1][2] for p in g.columns)
            assert all(g.positions(p)[-1]+g.height<=588.000001 for p in g.columns)
g=Solitaire(); g.columns=[[(1,0,True)],[(i,0,True) for i in range(13,1,-1)], *([[] for _ in range(8)])]
g.stock=[];g.completed=[0]*7
assert g.move(0,0,1) and g.won and g.over and len(g.completed)==8
m=Marble()
assert len(PATH)==241 and all(a<b for a,b in zip(PATH_LEN,PATH_LEN[1:]))
assert math.dist(path_at(PATH_LEN[-1]),PATH[-1])<1e-6
tracks=[]
for stage in range(1,len(MARBLE_TRACKS)+1):
    assert m.round==stage
    points,lengths=marble_path(stage)
    assert all(a<b for a,b in zip(lengths,lengths[1:]))
    assert all(30<x<870 and 112<y<590 for x,y in points)
    assert min(math.dist(p,m.gun) for p in points)>65
    assert math.dist(path_at(lengths[-1],points,lengths),points[-1])<1e-6
    tracks.append(tuple(points))
    m.chain=[1,1];m.current=m.next=1;m.hit(1,1)
assert m.won and m.over
assert len(set(tracks))==len(MARBLE_TRACKS)
print('Spider: 60 seeded deals, legal moves, undo, conservation and win. Marble: 12 distinct bounded tracks and every completion transition.')

