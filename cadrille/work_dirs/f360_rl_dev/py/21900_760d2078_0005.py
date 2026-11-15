import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-39,0))
r=w0.sketch().circle(100).finalize().extrude(70).union(w0.workplane(offset=73/2).cylinder(73,76.5)).union(w0.workplane(offset=77/2).cylinder(77,75))