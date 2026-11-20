import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-20,0))
r=w0.sketch().segment((-100,-100),(100,-100)).segment((100,100)).segment((-79.5,100)).segment((-100,100)).close().assemble().finalize().extrude(40).union(w0.workplane(offset=40/2).moveTo(77.5,49.5).box(43.5,11.5,40))