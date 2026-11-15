import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-27,0))
r=w0.sketch().segment((-40,-45),(72,-31)).arc((100,0),(72,31)).segment((-40,45)).close().assemble().push([(-54,0)]).circle(23,mode='s').push([(69,0)]).circle(15.5,mode='s').finalize().extrude(23).union(w0.sketch().push([(-52,0)]).circle(47.5).circle(23,mode='s').finalize().extrude(54))