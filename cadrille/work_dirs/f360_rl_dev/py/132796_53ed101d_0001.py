import cadquery as cq
w0=cq.Workplane('YZ',origin=(-82,0,0))
r=w0.workplane(offset=-18/2).cylinder(18,22).union(w0.workplane(offset=182/2).cylinder(182,11.5)).union(w0.workplane(offset=-18/2).box(1.5,1.5,1))