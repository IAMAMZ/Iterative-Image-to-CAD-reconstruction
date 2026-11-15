import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).box(100,8.5,200).union(w0.workplane(offset=-10/2).box(9.5,7,10))