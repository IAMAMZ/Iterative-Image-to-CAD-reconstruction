import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,9,0))
r=w0.sketch().rect(114,200).push([(-45,85)]).rect(6,6,mode='s').push([(0,-50)]).circle(3).push([(45,-85)]).rect(6,6,mode='s').push([(45,85)]).rect(6,6,mode='s').finalize().extrude(-17)