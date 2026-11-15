import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,11,0))
r=w0.sketch().segment((-43,0),(-15,-100)).segment((43,-100)).segment((43,100)).segment((-24,100)).segment((-43,49)).close().assemble().push([(0,-8)]).circle(7,mode='s').push([(0,68)]).circle(6.5,mode='s').finalize().extrude(-21)