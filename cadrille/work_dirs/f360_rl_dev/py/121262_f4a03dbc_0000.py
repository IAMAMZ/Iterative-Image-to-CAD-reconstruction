import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,31,0))
r=w0.sketch().circle(100).circle(81,mode='s').finalize().extrude(-61).union(w0.sketch().circle(100).circle(22.5,mode='s').finalize().extrude(-42))