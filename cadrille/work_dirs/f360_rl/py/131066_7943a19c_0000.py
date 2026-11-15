import cadquery as cq
w0=cq.Workplane('YZ',origin=(-1,0,0))
r=w0.workplane(offset=3/2).box(200,66.5,3).union(w0.workplane(offset=2/2).box(186.5,1.5,2))