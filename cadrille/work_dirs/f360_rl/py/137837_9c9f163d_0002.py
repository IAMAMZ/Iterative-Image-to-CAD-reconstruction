import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).box(29.5,20,200).union(w0.workplane(offset=-197/2).box(1.5,1.5,19)).union(w0.workplane(offset=-197/2).box(1.5,1.5,1))