import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,17))
r=w0.sketch().arc((-100,-2),(-3,-96),(92,-2)).segment((100,0)).segment((92,11)).arc((62,69),(0,96)).arc((-67,72),(-100,2)).close().assemble().finalize().extrude(-33.5)