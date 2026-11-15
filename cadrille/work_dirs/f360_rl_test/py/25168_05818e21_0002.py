import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,88))
r=w0.sketch().arc((-100,-2),(-8,-90),(81,-7)).segment((100,-3)).segment((100,4)).segment((81,7)).arc((-7,90),(-100,2)).close().assemble().finalize().extrude(-177)