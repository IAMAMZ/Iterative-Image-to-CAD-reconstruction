import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-0,0))
r=w0.sketch().segment((-30,-18),(30,-100)).segment((30,18)).segment((-30,100)).close().assemble().push([(0,0)]).circle(11.5,mode='s').finalize().extrude(2)