import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-86))
r=w0.workplane(offset=-14/2).cylinder(14,3).union(w0.sketch().arc((-24,-27),(0,-36),(24,-27)).segment((24,27)).arc((0,36),(-24,27)).close().assemble().finalize().extrude(169)).union(w0.workplane(offset=186/2).cylinder(186,2.5))