import cadquery as cq
w0=cq.Workplane('YZ',origin=(-1,0,0))
r=w0.workplane(offset=1.5/2).box(198,200,1.5).union(w0.workplane(offset=1/2).box(1,1.5,1))