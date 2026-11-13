import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().segment((-100,1),(-99,-8)).segment((100,-8)).segment((100,1)).segment((-1,1)).arc((-4,5),(-7,8)).segment((-7,1)).close().assemble().finalize().extrude(3)