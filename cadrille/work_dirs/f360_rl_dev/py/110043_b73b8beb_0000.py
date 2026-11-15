import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,56,0))
r=w0.workplane(offset=-111/2).cylinder(111,100).union(w0.workplane(offset=-30/2).cylinder(30,96))