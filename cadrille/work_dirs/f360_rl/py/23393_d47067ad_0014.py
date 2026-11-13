import cadquery as cq
w0=cq.Workplane('YZ',origin=(40,0,0))
r=w0.workplane(offset=-140/2).cylinder(140,13.5).union(w0.workplane(offset=60/2).cylinder(60,9)).union(w0.workplane(offset=60/2).cylinder(60,8))