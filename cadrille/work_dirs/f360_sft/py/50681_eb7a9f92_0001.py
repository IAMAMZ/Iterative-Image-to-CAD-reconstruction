import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-10,0))
r=w0.workplane(offset=20/2).cylinder(20,100).union(w0.sketch().circle(99).circle(87,mode='s').finalize().extrude(21))