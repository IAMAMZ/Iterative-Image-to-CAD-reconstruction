import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,1,0))
r=w0.sketch().segment((-52,-100),(52,-100)).segment((52,94)).arc((46,96),(52,98)).segment((52,100)).segment((-52,100)).close().assemble().push([(-47,92)]).circle(3,mode='s').push([(-46,-94)]).circle(4,mode='s').push([(48,-93)]).circle(3,mode='s').finalize().extrude(-3)