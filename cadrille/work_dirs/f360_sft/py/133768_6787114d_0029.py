import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.workplane(offset=40/2).cylinder(40,100)