import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-27,0))
r=w0.workplane(offset=-55/2).moveTo(62,-46).cylinder(55,38).union(w0.workplane(offset=109/2).moveTo(-62,45).cylinder(109,38))