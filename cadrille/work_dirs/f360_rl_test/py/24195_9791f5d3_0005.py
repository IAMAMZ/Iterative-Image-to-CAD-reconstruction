import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,15,0))
r=w0.sketch().circle(100).circle(83.5,mode='s').circle(83.5).circle(80,mode='s').finalize().extrude(-29.5)