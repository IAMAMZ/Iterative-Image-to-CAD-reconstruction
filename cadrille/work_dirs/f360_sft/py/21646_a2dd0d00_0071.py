import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-12,0))
r=w0.sketch().circle(100).circle(28,mode='s').finalize().extrude(25)