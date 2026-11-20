import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,17,0))
r=w0.sketch().arc((-33.5,-66),(0,-100),(34,-66)).segment((30.5,70)).arc((-1,100),(-29,73)).close().assemble().push([(0,-66)]).circle(17,mode='s').push([(0,70)]).circle(12.5,mode='s').finalize().extrude(-34)