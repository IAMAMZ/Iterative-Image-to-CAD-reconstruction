import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,24,0))
r=w0.sketch().segment((-24,61),(-1,-100)).segment((24,61)).arc((15,78),(12,98)).segment((1,100)).segment((-1,100)).segment((-24,62)).close().assemble().finalize().extrude(-48)