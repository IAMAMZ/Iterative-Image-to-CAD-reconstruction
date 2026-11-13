import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,85,0))
r=w0.sketch().segment((-100,-84),(100,-84.5)).segment((100,84.5)).segment((-64.5,84.5)).segment((-100,84.5)).close().assemble().finalize().extrude(-170)