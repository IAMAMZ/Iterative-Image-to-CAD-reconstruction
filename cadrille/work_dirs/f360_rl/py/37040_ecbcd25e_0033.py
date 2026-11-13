import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-3,-33),(-1,-35)).segment((3,-34)).segment((3,35)).segment((-1.5,34)).segment((-2,-31)).close().assemble().finalize().extrude(-200).union(w0.workplane(offset=-2/2).box(1.5,1.5,1))