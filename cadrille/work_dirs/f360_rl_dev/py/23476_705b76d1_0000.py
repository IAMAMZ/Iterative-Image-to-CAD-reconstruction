import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-61,0))
r=w0.workplane(offset=10/2).cylinder(10,100).union(w0.workplane(offset=8/2).cylinder(8,99)).union(w0.sketch().circle(100).circle(93.5,mode='s').finalize().extrude(122))