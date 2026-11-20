import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,80,0))
r=w0.sketch().segment((-100,-95),(100,-95)).segment((100,95)).segment((-69.5,95)).segment((-100,95)).close().assemble().finalize().extrude(-160)