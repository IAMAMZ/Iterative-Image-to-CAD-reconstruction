import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).cylinder(200,22).union(w0.workplane(offset=-103/2).moveTo(0,8).box(180,28,103)).union(w0.workplane(offset=-100/2).moveTo(0,8).box(19.5,19.5,100)).union(w0.workplane(offset=-100/2).moveTo(0,8).box(10.5,1.5,7))