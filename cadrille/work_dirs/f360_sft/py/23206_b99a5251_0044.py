import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,52,0))
r=w0.sketch().segment((-87,-50),(-1,-100)).segment((6,-90)).segment((87,-50)).segment((87,50)).segment((1,100)).segment((-6,90)).segment((-87,50)).close().assemble().finalize().extrude(-104)