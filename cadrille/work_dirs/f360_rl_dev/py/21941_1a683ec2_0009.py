import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,11))
r=w0.sketch().circle(100).push([(0,-43)]).circle(15,mode='s').push([(0,43)]).circle(15,mode='s').finalize().extrude(-22)