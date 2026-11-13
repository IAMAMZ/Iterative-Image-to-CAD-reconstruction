import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-36,0))
r=w0.workplane(offset=72/2).cylinder(72,100)