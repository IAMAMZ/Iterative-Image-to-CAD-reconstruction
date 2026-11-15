import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,50))
w1=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.workplane(offset=-100/2).moveTo(-52,-48).cylinder(100,33.5).union(w0.sketch().segment((-50,-100),(84,0)).segment((-50,0)).close().assemble().finalize().extrude(-100)).union(w1.workplane(offset=101/2).moveTo(0,17).cylinder(101,33.5)).union(w1.workplane(offset=-77/2).moveTo(0,-52.5).box(1.5,1.5,7))