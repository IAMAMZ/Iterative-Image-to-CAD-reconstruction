import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).box(27.5,9,200).union(w0.workplane(offset=-199/2).box(19.5,9,19)).union(w0.workplane(offset=-199/2).box(1.5,7.5,1))