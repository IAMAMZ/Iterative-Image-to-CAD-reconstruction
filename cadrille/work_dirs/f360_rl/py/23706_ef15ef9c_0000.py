import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,11))
r=w0.sketch().segment((-16.5,42),(-6,35)).segment((-6,-100)).segment((16.5,-100)).segment((16.5,100)).segment((-16,100)).close().assemble().finalize().extrude(-21)