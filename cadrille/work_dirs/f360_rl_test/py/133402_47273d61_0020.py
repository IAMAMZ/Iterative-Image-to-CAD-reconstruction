import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).moveTo(0,0).box(10,10,200).union(w0.workplane(offset=-2/2).box(9.5,7.5,1))