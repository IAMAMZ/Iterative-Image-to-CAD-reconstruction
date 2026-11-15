import cadquery as cq
w0=cq.Workplane('YZ',origin=(81,0,0))
r=w0.workplane(offset=-163/2).cylinder(163,100).union(w0.workplane(offset=-10/2).cylinder(10,96))