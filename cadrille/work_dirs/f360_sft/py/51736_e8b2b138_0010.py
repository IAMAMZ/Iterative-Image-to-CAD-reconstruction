import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-8,0))
r=w0.sketch().circle(100).circle(87,mode='s').finalize().extrude(16)