import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,68))
r=w0.workplane(offset=-136/2).cylinder(136,100)