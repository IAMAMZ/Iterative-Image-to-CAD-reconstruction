import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,31))
r=w0.sketch().arc((-100,-2),(-10,-91),(83,-6)).segment((100,-3)).segment((100,4)).segment((83,6)).arc((-7,91),(-100,2)).close().assemble().finalize().extrude(-61)