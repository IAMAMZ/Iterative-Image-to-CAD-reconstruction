import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-2,0))
r=w0.workplane(offset=4/2).cylinder(4,100)