import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.workplane(offset=-52/2).cylinder(52,100).union(w0.sketch().segment((-73,-42),(1,-84)).segment((73,-41.5)).segment((73,42)).segment((0,84)).segment((-73,41)).close().assemble().finalize().extrude(42))