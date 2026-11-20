import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,58,0))
w1=cq.Workplane('ZX',origin=(0,-59,0))
r=w0.sketch().circle(50).circle(32.5,mode='s').finalize().extrude(-158).union(w0.sketch().circle(77).circle(33.5,mode='s').finalize().extrude(42)).union(w1.sketch().circle(77.5).circle(33.5,mode='s').finalize().extrude(-41))