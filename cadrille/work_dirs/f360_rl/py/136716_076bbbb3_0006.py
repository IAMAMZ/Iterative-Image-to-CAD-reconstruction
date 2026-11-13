import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).moveTo(0,-0).box(6.5,62.5,200).union(w0.workplane(offset=-2/2).box(6.5,1.5,1))