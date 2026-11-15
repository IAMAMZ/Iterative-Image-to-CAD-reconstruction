import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).box(14.5,18,200).union(w0.workplane(offset=-20/2).box(13.5,1.5,20))