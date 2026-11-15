import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-21,0))
r=w0.sketch().circle(100).finalize().extrude(15).union(w0.workplane(offset=41/2).cylinder(41,42))