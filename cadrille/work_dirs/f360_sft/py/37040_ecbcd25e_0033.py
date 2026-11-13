import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().segment((-3,-32),(3,-35)).segment((3,35)).segment((-3,35)).segment((-3,32)).segment((0,32)).segment((0,-32)).close().assemble().finalize().extrude(200)