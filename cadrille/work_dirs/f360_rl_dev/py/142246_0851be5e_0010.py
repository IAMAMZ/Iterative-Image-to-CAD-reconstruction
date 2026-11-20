import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-23,0))
r=w0.sketch().segment((-71,-92),(-63,-100)).segment((33,-100)).segment((47,-49)).segment((-16,-47)).segment((-16,88.5)).arc((-32,99),(-45,83)).segment((-70,14)).segment((-71,-1)).close().assemble().finalize().extrude(14).union(w0.workplane(offset=47/2).moveTo(43,-72).cylinder(47,28))