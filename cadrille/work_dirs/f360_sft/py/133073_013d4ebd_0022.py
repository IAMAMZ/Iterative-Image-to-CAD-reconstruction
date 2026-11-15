import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-5,0))
r=w0.workplane(offset=10/2).cylinder(10,100)