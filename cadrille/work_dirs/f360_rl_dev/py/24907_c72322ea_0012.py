import cadquery as cq
w0=cq.Workplane('YZ',origin=(3,0,0))
r=w0.sketch().segment((-39,-91),(-19,-96)).arc((21,-95),(39,-64)).segment((39,60)).segment((39,64)).arc((22,95),(-12,97)).segment((-20,93)).segment((-40,74)).segment((-39,62)).segment((-10,50)).segment((-10,-49)).segment((-39,-63.5)).close().assemble().finalize().extrude(-5.5)