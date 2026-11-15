import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-10,0))
r=w0.workplane(offset=5/2).cylinder(5,100).union(w0.sketch().circle(100).circle(96.5,mode='s').finalize().extrude(20))