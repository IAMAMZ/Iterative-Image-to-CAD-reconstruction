import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-4,-4),(4,-4)).segment((4,4)).segment((-4,4)).segment((-4,2)).arc((0,0),(-4,-2)).close().assemble().finalize().extrude(-200)