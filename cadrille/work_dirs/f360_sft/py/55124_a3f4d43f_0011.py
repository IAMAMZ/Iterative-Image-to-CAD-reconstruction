import cadquery as cq
w0=cq.Workplane('YZ',origin=(-88,0,0))
r=w0.workplane(offset=-12/2).cylinder(12,47).union(w0.workplane(offset=188/2).cylinder(188,31))