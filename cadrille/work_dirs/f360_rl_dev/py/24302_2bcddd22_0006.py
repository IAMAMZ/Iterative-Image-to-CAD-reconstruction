import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-44,0))
r=w0.workplane(offset=-50/2).cylinder(50,20).union(w0.sketch().circle(100).finalize().extrude(18.5)).union(w0.workplane(offset=138/2).cylinder(138,31))