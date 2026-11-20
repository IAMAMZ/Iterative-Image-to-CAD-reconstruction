import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-78,0))
r=w0.sketch().segment((-32,-4),(-12,-31)).segment((21,-28)).segment((32,4)).segment((12,31)).segment((-21,28)).close().assemble().finalize().extrude(-22).union(w0.workplane(offset=178/2).cylinder(178,17.5)).union(w0.workplane(offset=178/2).box(1.5,1.5,7))