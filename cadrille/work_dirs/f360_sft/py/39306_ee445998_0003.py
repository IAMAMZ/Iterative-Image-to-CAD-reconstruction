import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-73,0))
r=w0.workplane(offset=-27/2).cylinder(27,100).union(w0.workplane(offset=173/2).cylinder(173,66))