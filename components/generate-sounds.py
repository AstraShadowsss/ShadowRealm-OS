#!/usr/bin/python3
"""Generate original, quiet ShadowRealm-OS chimes. MIT; no samples."""
import math,wave,struct
from pathlib import Path
import sys
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
for name,notes,duration in [('desktop-login',[392,493.88,587.33],1.3),('desktop-logout',[587.33,493.88,392],1.15),('alarm-clock-elapsed',[523.25,659.25,783.99,659.25],3),('gentle',[440,554.37,659.25],4),('pulse',[660,660,880,880],3)]:
 rate=22050;data=bytearray()
 for i in range(int(rate*duration)):
  t=i/rate;slot=duration/len(notes);n=min(len(notes)-1,int(t/slot));local=t-n*slot
  env=(1-math.exp(-local*55))*math.exp(-local*5)*min(1,(duration-t)*12)
  v=.20*env*(math.sin(2*math.pi*notes[n]*t)+.16*math.sin(4*math.pi*notes[n]*t))
  data.extend(struct.pack('<h',int(32767*v)))
 with wave.open(str(out/(name+'.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)
