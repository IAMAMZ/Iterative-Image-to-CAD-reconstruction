import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,35))
w1=cq.Workplane('ZX',origin=(0,11,0))
r=w0.sketch().segment((-24,-23),(24,-23)).segment((24,78)).segment((23,78)).arc((-1,100),(-24,78)).close().assemble().finalize().extrude(-70).union(w0.workplane(offset=-7/2).moveTo(0,67).cylinder(7,33)).union(w1.workplane(offset=-111/2).cylinder(111,8))