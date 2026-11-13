import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-5,0))
r=w0.sketch().segment((-100,-100),(100,-100)).segment((100,100)).segment((56,100)).arc((-2,42),(-56,100)).segment((-100,100)).close().assemble().reset().face(w0.sketch().segment((-91,-36),(-33,-94)).segment((-18,-80)).segment((-76,-22)).close().assemble(),mode='s').finalize().extrude(10)