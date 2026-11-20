import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,19,0))
r=w0.sketch().circle(100).circle(88,mode='s').circle(63).circle(50,mode='s').finalize().extrude(-39)