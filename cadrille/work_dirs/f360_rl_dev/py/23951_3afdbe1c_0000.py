import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-40))
r=w0.sketch().circle(100).circle(48,mode='s').finalize().extrude(11).union(w0.sketch().circle(100).circle(88,mode='s').finalize().extrude(80))