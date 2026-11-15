import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,23))
r=w0.sketch().arc((-100,-2),(-10,-91),(82,-8)).segment((100,-4)).segment((100,5)).segment((82.5,7)).arc((0,91),(-100,2)).close().assemble().finalize().extrude(-45.5)