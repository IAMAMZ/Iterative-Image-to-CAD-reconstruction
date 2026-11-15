import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).cylinder(200,22).union(w0.workplane(offset=-103/2).moveTo(0,8.5).box(178,27,103))