import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-7,0))
r=w0.sketch().arc((-16,-86),(0,-100),(16,-86)).segment((16,86)).segment((15,86)).arc((-1,100),(-16,86)).close().assemble().push([(-1,82)]).circle(11,mode='s').push([(0,-82)]).circle(11,mode='s').finalize().extrude(15)