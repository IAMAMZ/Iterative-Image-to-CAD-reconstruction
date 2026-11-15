import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,6,0))
r=w0.sketch().segment((-100,-100),(100,-100)).segment((100,100)).segment((56,100)).arc((0,43),(-56,100)).segment((-100,100)).close().assemble().reset().face(w0.sketch().segment((-92,-40),(-33,-93)).segment((-19,-81)).segment((-73,-18)).close().assemble(),mode='s').finalize().extrude(-10)