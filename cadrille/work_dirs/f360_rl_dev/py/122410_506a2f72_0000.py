import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,28,0))
r=w0.sketch().segment((-100,-33),(-33,-100)).segment((100,33)).segment((33,100)).close().assemble().finalize().extrude(-55)