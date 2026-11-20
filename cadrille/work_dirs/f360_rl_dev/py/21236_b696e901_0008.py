import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-53,-60),(-52,-60)).arc((4,-79),(53,-60)).segment((53,60)).arc((0,79),(-53,60)).close().assemble().finalize().extrude(-200)