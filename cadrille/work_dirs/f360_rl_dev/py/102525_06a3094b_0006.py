import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).box(108,28,200).union(w0.workplane(offset=-109/2).box(10.5,1.5,109)).union(w0.workplane(offset=-109/2).box(10.5,1.5,10))