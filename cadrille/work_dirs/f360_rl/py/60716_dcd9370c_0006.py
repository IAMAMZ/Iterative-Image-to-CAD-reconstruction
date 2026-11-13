import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).moveTo(0,0).cylinder(200,10).union(w0.workplane(offset=-199/2).cylinder(19,9.5))