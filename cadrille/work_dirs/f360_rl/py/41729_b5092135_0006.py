import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,51,0))
r=w0.sketch().segment((-44,96),(38,15)).segment((37,-94)).segment((-5.5,-94)).segment((-5,-100)).segment((44,-100)).segment((44,17)).segment((-39,100)).close().assemble().finalize().extrude(-100)