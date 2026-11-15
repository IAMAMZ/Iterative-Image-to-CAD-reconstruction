import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-45,-46),(-4,-46)).segment((-4,-100)).segment((45,-100)).segment((45,100)).segment((-4,100)).segment((-4,52)).segment((-45,52)).close().assemble().finalize().extrude(14)