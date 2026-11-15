import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).moveTo(0,0).cylinder(200,25).union(w0.workplane(offset=-10/2).cylinder(10,4.5))