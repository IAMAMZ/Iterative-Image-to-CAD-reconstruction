import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).moveTo(0,0).box(12,11,200).union(w0.workplane(offset=-2/2).box(11.5,9.5,1))