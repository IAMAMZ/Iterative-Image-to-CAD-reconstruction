import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,6.5,0))
w1=cq.Workplane('ZX',origin=(0,13,0))
r=w0.sketch().segment((-71,-100),(71.5,-100)).segment((71,39)).segment((71,100)).segment((-71,100)).close().assemble().finalize().extrude(-20).union(w1.workplane(offset=-2/2).moveTo(69.5,-37.5).box(2,2.5,2))