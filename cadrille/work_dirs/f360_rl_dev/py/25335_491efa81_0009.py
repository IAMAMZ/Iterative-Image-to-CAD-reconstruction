import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.workplane(offset=-10/2).moveTo(0,-45).cylinder(10,55).union(w0.workplane(offset=40/2).moveTo(0,37.5).box(25,126,40))