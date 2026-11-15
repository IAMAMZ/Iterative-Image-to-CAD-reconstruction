import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).box(133.5,9,200).union(w0.workplane(offset=-10/2).box(12.5,7.5,10))