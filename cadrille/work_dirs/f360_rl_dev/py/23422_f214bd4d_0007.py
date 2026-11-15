import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,8))
r=w0.sketch().arc((-100,-6),(-2,-96),(93,-2)).segment((100,0)).segment((93,6)).arc((-4,97),(-100,4)).close().assemble().finalize().extrude(-15.5)