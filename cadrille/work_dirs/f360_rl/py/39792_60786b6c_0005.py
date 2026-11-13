import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,25,0))
r=w0.workplane(offset=-50/2).moveTo(10,-71).cylinder(50,20).union(w0.sketch().arc((-41,73),(-8,16),(-18,-63)).arc((9,-100),(38,-67)).segment((37,-29)).arc((31,27),(6,80)).arc((-19,100),(-41,75)).close().assemble().finalize().extrude(-10.5))