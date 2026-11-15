import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-32,0))
r=w0.sketch().segment((-49,54),(-42,46)).arc((48,57),(-43,63)).close().assemble().finalize().extrude(2).union(w0.workplane(offset=65/2).moveTo(-2,-58).cylinder(65,41))