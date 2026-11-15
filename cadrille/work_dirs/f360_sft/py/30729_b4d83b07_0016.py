import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().segment((-5,-4),(-1,-4)).segment((-1,-1)).segment((3,-1)).segment((3,-4)).segment((5,-4)).segment((5,4)).segment((-5,4)).close().assemble().finalize().extrude(200)