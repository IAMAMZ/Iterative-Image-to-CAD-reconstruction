import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-62,0))
r=w0.sketch().segment((-46,-26),(-3,-53)).segment((1,-47)).segment((46,-27)).segment((46,26)).segment((3,53)).segment((-1,47)).segment((-46,27)).close().assemble().finalize().extrude(-38).union(w0.workplane(offset=162/2).moveTo(3,0).cylinder(162,27))