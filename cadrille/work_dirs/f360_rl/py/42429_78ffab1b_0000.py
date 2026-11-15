import cadquery as cq
w0=cq.Workplane('YZ',origin=(-70,0,0))
r=w0.workplane(offset=-30/2).cylinder(30,30).union(w0.workplane(offset=170/2).cylinder(170,7.5)).union(w0.workplane(offset=-8/2).box(1.5,1.5,1)).union(w0.workplane(offset=17/2).box(1.5,1.5,2))