"""Behavior checks for ordinary Spider stack transfers, not just single cards."""
from classics import Solitaire

def board():
 g=Solitaire();g.columns=[[(6,0,True),(5,0,True),(4,0,True)],[(7,1,True)],*([[] for _ in range(8)])]
 g.stock=[];g.completed=[];g.undo=[];return g
g=board();before=[p[:] for p in g.columns]
assert g.movable(0,0) and g.move(0,0,1)
assert not g.columns[0] and g.columns[1]==[(7,1,True),*before[0]]
g.step(0,{'u'});assert g.columns==before,'Undo must restore every moved card'
g=board();assert g.move(0,1,2) and g.columns[2]==[(5,0,True),(4,0,True)]
g=board();g.columns[0][1]=(5,1,True)
assert not g.movable(0,0) and not g.move(0,0,1),'Mixed-suit runs cannot travel together'
g=board();g.columns[0][1]=(3,0,True)
assert not g.movable(0,0),'Ranks must descend without gaps'
g=board();g.columns[0][0]=(6,0,False)
assert not g.movable(0,0),'Face-down cards cannot be grabbed'
g=board();g.columns[1]=[(8,0,True)];assert not g.move(0,0,1),'Destination must be exactly one rank higher'
g=board();g.stock=[(2,0,False)]*10;g.deal();assert len(g.stock)==10,'Fill empty columns before dealing'
print('PASS Spider: whole suited stacks, partial stacks, empty columns, undo, mixed-suit/rank/face-down rejection and stock rule')
