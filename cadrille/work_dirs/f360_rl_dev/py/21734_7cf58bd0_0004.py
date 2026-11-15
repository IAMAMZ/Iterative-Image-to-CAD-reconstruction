import cadquery as cq
w0=cq.Workplane('YZ',origin=(3,0,0))
r=w0.workplane(offset=-103/2).cylinder(103,3).union(w0.workplane(offset=-25/2).box(29.5,11,25)).union(w0.workplane(offset=-25/2).box(2.5,9.5,25)).union(w0.workplane(offset=97/2).cylinder(97,3)).union(w0.workplane(offset=-19/2).box(1.5,1.5,1))