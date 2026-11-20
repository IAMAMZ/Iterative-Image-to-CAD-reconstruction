import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,6))
r=w0.sketch().segment((-100,-23),(78,-23)).arc((100,0),(78,23)).segment((-78,23.5)).segment((-100,23)).close().assemble().finalize().extrude(-11.5)