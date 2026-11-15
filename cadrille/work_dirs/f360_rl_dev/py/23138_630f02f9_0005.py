import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-25))
r=w0.sketch().circle(100).finalize().extrude(13).union(w0.workplane(offset=52/2).cylinder(52,66))