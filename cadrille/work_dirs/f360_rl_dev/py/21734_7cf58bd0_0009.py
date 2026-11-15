import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
w1=cq.Workplane('YZ',origin=(79,0,0))
r=w0.workplane(offset=-31/2).cylinder(31,14).union(w1.workplane(offset=-179/2).cylinder(179,6.5)).union(w1.workplane(offset=21/2).box(22.5,21.5,21))