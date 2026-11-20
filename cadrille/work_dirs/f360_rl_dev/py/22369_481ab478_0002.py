import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,34,0))
r=w0.sketch().segment((-36.5,-100),(-14,-100)).segment((-14,-33)).segment((6,-31)).segment((9,-27)).arc((36,2),(0,26)).segment((-12,31)).segment((-14,43)).segment((-14,100)).segment((-36,100)).close().assemble().push([(9,0)]).circle(16,mode='s').finalize().extrude(-66.5)