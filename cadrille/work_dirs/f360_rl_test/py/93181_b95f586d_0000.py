import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-27,0))
r=w0.workplane(offset=-54/2).moveTo(62,-45).cylinder(54,38).union(w0.workplane(offset=109/2).moveTo(-62,45).cylinder(109,38)).union(w0.workplane(offset=10/2).moveTo(62,-45.5).box(1,1,1))