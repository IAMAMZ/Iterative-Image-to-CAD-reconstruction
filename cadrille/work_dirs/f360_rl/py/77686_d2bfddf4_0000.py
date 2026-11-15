import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,2))
r=w0.workplane(offset=-5/2).box(200,200,5).union(w0.workplane(offset=-3/2).box(186.5,18.5,3))