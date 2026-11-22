"""Pinball physics and multiball bounds without changing player saves."""
import importlib.util, math, random, sys, tempfile
from pathlib import Path
source=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('pinball_rules',source)
pin=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pin;spec.loader.exec_module(pin)
with tempfile.TemporaryDirectory() as state:
    pin.SAVE=Path(state)/'scores.json'
    table=pin.Table();table.launch();table.bank=set(range(len(pin.TARGETS)));table.advance()
    assert len(table.balls)==3 and table.multiball_used
    table.balls=table.balls[:1];table.bank=set(range(len(pin.TARGETS)));table.advance()
    assert len(table.balls)==1,'Multiball retriggered before the next ball'
    table=pin.Table();table.ball_save=0
    for remaining in [2,1,0]:
        table.balls=[];table.advance();assert table.remaining==remaining
    assert table.over
    for seed in range(12):
        rng=random.Random(seed);table=pin.Table();table.launch()
        for frame in range(240*30):
            if frame%48==0:
                table.keys={key for key in ['Shift_L','Shift_R'] if rng.random()<.55}
            if any(ball.staged for ball in table.balls):table.launch()
            table.advance()
            assert len(table.balls)<=3
            assert all(math.isfinite(value) for ball in table.balls for value in [ball.x,ball.y,ball.vx,ball.vy])
            if table.over:break
print('PASS multiball cap, no repeated trigger, three-ball finish and twelve finite physics simulations')
