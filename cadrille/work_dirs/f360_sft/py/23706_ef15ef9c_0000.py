import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-16,45),(-12,36)).segment((-6,36)).segment((-6,-100)).segment((16,-100)).segment((16,100)).segment((-16,100)).close().assemble().finalize().extrude(22)