import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().arc((-18,-83),(0,-100),(17.5,-83)).segment((18,83)).arc((0,100),(-18,83)).close().assemble().push([(0,-83)]).circle(11,mode='s').push([(0,83)]).circle(11,mode='s').finalize().extrude(-14)