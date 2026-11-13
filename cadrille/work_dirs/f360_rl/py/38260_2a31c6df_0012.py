import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,8,0))
r=w0.sketch().rect(100,200).push([(16,71)]).circle(12.5,mode='s').push([(15,-71)]).circle(12.5,mode='s').finalize().extrude(-14.5)