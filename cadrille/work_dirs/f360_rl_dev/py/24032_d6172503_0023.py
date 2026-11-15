import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-75,0))
r=w0.sketch().segment((-45,-20),(-5,-50)).segment((36,-33)).segment((45,-11)).segment((44,20)).segment((5,50)).segment((-36,33)).segment((-43.5,19)).close().assemble().finalize().extrude(-25.5).union(w0.workplane(offset=175/2).moveTo(0,0).cylinder(175,22)).union(w0.workplane(offset=-2/2).moveTo(0,0.5).box(1.5,1.5,1))