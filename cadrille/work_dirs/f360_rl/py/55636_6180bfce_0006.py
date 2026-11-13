import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().segment((-100,-100),(-87,-100)).segment((0,87)).segment((87,-100)).segment((100,-100)).segment((4,92)).segment((0,100)).segment((-3,92)).close().assemble().reset().face(w0.sketch().segment((-14,67),(44,-17.5)).segment((47.5,-14.5)).segment((8,84)).close().assemble(),mode='s').finalize().extrude(-12.5)