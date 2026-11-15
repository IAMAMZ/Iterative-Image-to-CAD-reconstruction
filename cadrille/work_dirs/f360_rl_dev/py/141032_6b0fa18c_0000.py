import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,34))
r=w0.workplane(offset=-67/2).box(200,100,67).union(w0.workplane(offset=-37/2).box(186.5,89.5,37))