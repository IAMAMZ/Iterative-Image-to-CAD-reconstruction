import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-2,0))
r=w0.sketch().arc((-13,-68),(0,-100),(12,-68)).segment((11,64.5)).arc((0,100),(-11.5,65)).segment((-11,-64.5)).close().assemble().push([(0,-81)]).circle(9,mode='s').push([(0,82)]).circle(9,mode='s').finalize().extrude(3.5)