import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-89,0))
r=w0.workplane(offset=-11/2).cylinder(11,18).union(w0.workplane(offset=189/2).cylinder(189,12.5)).union(w0.workplane(offset=-11/2).box(1.5,1.5,2.5)).union(w0.workplane(offset=189/2).box(1.5,1.5,1))