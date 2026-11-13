import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().segment((-45,-44),(-3,-44)).segment((-3,-100)).segment((45.5,-100)).segment((45.5,100)).segment((-3,100)).segment((-3.5,52)).segment((-45,52)).close().assemble().finalize().extrude(-12.5)