import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().arc((-3,48),(23,48),(47,38)).segment((61,62)).segment((1,88)).close().assemble().finalize().extrude(-43).union(w0.sketch().circle(100).reset().face(w0.sketch().segment((-21,-86),(-10,-86)).segment((-10,-52)).arc((0,52),(-21,-50)).close().assemble(),mode='s').circle(34).finalize().extrude(53))