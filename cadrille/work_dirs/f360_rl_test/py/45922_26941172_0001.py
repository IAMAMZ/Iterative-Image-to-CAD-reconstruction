import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).cylinder(200,18).union(w0.sketch().segment((-24,5),(-10,-23)).segment((24,-11)).segment((10,23)).segment((-10,21)).close().assemble().finalize().extrude(-19)).union(w0.workplane(offset=-8/2).box(1.5,1.5,7))