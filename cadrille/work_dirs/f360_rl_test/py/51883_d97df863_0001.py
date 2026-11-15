import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().circle(100).circle(60.5,mode='s').finalize().extrude(-14)