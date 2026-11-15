import cadquery as cq
w0=cq.Workplane('YZ',origin=(-85,0,0))
w1=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.workplane(offset=185/2).cylinder(185,8.5).union(w1.workplane(offset=2/2).box(4.5,8.5,2))