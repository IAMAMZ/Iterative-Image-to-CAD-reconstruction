import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().segment((-40,-100),(37.5,-100)).segment((40,-94)).segment((40,94)).segment((37,100)).segment((-40,100)).close().assemble().finalize().extrude(-10)