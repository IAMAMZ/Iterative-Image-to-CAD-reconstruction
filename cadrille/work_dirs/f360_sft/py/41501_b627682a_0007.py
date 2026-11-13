import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-3,0))
r=w0.sketch().segment((-5,-97),(4,-97)).segment((4,97)).segment((1,97)).arc((-2,100),(-5,97)).close().assemble().push([(0,-95)]).circle(5,mode='s').finalize().extrude(7)