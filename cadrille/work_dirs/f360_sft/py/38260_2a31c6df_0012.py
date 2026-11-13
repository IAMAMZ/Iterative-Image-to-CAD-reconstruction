import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().rect(100,200).push([(15,-71)]).circle(13,mode='s').push([(15,71)]).circle(13,mode='s').finalize().extrude(-14)