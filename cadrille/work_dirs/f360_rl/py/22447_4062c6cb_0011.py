import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,43,0))
r=w0.workplane(offset=-87/2).cylinder(87,62).union(w0.workplane(offset=-25/2).cylinder(25,85)).union(w0.sketch().circle(100).finalize().extrude(-13))