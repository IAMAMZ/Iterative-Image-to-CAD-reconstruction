import cadquery as cq
w0=cq.Workplane('YZ',origin=(-42,0,0))
w1=cq.Workplane('YZ',origin=(42.5,0,0))
r=w0.workplane(offset=5/2).moveTo(0,0).box(133.5,200,5).union(w0.workplane(offset=6/2).moveTo(-64.5,69.5).box(1.5,1.5,6)).union(w1.workplane(offset=-39/2).moveTo(-64.5,0.5).box(1.5,1,39)).union(w1.workplane(offset=-19/2).moveTo(-64.5,69.5).box(1.5,1.5,19))