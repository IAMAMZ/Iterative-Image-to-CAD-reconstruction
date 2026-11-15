import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,47,0))
r=w0.sketch().segment((25,-100),(35,-100)).segment((35,-62)).arc((-27,-6),(28,60)).segment((35,61)).segment((35,100)).segment((25,100)).segment((25,67)).arc((-35,-3),(25,-69)).close().assemble().finalize().extrude(-92)