import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,46,0))
r=w0.sketch().segment((26,-100),(35,-100)).segment((35,-62)).arc((-29,0),(35,62)).segment((35,100)).segment((26,100)).segment((26,61)).arc((-35,0),(26,-61)).close().assemble().finalize().extrude(-92)