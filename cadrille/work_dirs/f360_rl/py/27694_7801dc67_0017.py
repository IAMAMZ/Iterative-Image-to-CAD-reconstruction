import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-85,0))
w1=cq.Workplane('ZX',origin=(0,78,0))
r=w0.workplane(offset=-15/2).cylinder(15,46).union(w0.workplane(offset=185/2).cylinder(185,12.5)).union(w1.workplane(offset=-9.5/2).cylinder(9.5,31.5)).union(w1.workplane(offset=-7/2).cylinder(7,2.5))