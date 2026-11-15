import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-63,0))
r=w0.sketch().segment((-46,-26),(0,-53)).segment((46,-26)).segment((46,26)).segment((0,53)).segment((-46,26)).close().assemble().finalize().extrude(-37).union(w0.workplane(offset=163/2).moveTo(3,0).cylinder(163,27))