import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.workplane(offset=13/2).cylinder(13,47).union(w0.workplane(offset=200/2).cylinder(200,31.5))