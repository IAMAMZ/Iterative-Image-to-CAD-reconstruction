import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,12,0))
r=w0.sketch().segment((-100,0),(-1,0)).segment((0,-100)).segment((100,-100)).segment((100,100)).segment((-69.5,100)).segment((-100,100)).close().assemble().finalize().extrude(-25)