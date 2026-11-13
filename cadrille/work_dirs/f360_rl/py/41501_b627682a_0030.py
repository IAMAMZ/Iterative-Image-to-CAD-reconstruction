import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-20,0))
r=w0.sketch().segment((-20,-12),(55,-100)).segment((55,100)).segment((-19,6.5)).close().assemble().finalize().extrude(9.5).union(w0.workplane(offset=40/2).moveTo(-35,0).cylinder(40,20))