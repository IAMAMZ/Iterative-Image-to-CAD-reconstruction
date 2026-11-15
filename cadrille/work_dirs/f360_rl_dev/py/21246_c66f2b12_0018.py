import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,19,0))
r=w0.sketch().segment((-78,-78),(78,-100)).segment((78,100)).segment((-78,78)).close().assemble().finalize().extrude(-37.5)