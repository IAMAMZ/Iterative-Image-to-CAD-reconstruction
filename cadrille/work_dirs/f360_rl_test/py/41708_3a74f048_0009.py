import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-5,0))
r=w0.sketch().segment((-79,-10),(0,-10)).segment((100,-2.5)).segment((99,2)).segment((-1.5,10)).segment((-79,10)).close().assemble().finalize().extrude(4).union(w0.workplane(offset=9.5/2).moveTo(-89,0).box(21.5,21,9)).union(w0.workplane(offset=9/2).moveTo(-90,7.5).box(5,1.5,9))