import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().arc((-21,0),(-5,-3),(10,0)).segment((9,0)).arc((-5,-2),(-19,0)).close().assemble().reset().face(w0.sketch().segment((17,0),(21,0)).arc((20,2),(19,3)).arc((18,2),(17,0)).assemble()).finalize().extrude(-200)