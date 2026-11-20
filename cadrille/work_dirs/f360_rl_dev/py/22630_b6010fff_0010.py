import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,3,0))
r=w0.sketch().circle(100).circle(95,mode='s').finalize().extrude(-6)