import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,16,0))
r=w0.workplane(offset=-32/2).moveTo(-77,40.5).box(8,45.5,32).union(w0.sketch().segment((-100,-83),(100,0)).segment((-100,83)).close().assemble().push([(-79,0)]).circle(6,mode='s').finalize().extrude(-16))