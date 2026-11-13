import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,50))
w1=cq.Workplane('ZX',origin=(0,-33,0))
r=w0.sketch().segment((-50,-100),(83,0)).segment((-50,0)).close().assemble().finalize().extrude(-100).union(w0.workplane(offset=-81/2).moveTo(-27,-50).cylinder(81,33)).union(w1.workplane(offset=133/2).moveTo(0,17).cylinder(133,33))