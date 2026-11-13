import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,16))
w1=cq.Workplane('ZX',origin=(0,42,0))
r=w0.workplane(offset=-50/2).moveTo(57,95).box(80,10,50).union(w0.workplane(offset=-33/2).moveTo(-52,-87).box(90.5,26,33)).union(w0.sketch().segment((-20,75),(30.5,75)).segment((30.5,83)).segment((-1.5,83)).segment((-20,80)).close().assemble().finalize().extrude(18)).union(w1.workplane(offset=-110/2).moveTo(-5,-57).cylinder(110,7))