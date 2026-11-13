import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-85,0))
w1=cq.Workplane('ZX',origin=(0,70,0))
r=w0.workplane(offset=-15/2).cylinder(15,46).union(w0.workplane(offset=185/2).cylinder(185,8)).union(w1.workplane(offset=10/2).cylinder(10,30))