import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,8))
r=w0.sketch().arc((-100,-6),(-7,-91),(81,-7)).segment((100,-4)).segment((100,6)).segment((81,6)).arc((-10,91),(-100,6)).close().assemble().finalize().extrude(-15)