import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,83))
r=w0.workplane(offset=-183/2).cylinder(183,4).union(w0.sketch().arc((-25,-27),(0,-36),(25,-27)).segment((25,27)).segment((23,27)).arc((0,36),(-23,27)).segment((-25,27)).close().assemble().finalize().extrude(-169)).union(w0.workplane(offset=17/2).cylinder(17,3))