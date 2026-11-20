import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.workplane(offset=-200/2).cylinder(200,11).union(w0.sketch().segment((-23,0),(-12,-20)).segment((12,-20)).segment((23,0)).segment((12,20)).segment((-12,20)).close().assemble().finalize().extrude(-18)).union(w0.workplane(offset=-17/2).box(1.5,1.5,1))