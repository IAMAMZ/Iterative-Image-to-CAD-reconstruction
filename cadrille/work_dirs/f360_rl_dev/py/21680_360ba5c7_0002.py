import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-76,0))
r=w0.sketch().segment((-30,0),(-15,-27)).segment((18,-27)).segment((30,0)).segment((15,27)).segment((-18,27)).close().assemble().finalize().extrude(-24).union(w0.workplane(offset=176/2).cylinder(176,18))