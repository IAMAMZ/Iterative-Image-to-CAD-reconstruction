import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).cylinder(200,78.5).union(w0.workplane(offset=-100/2).box(12.5,13.5,100))