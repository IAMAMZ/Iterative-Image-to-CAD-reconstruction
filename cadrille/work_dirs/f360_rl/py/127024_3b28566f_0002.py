import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().segment((-30,-97),(29,-100)).segment((30,97)).segment((-9,100)).segment((-30,97)).close().assemble().finalize().extrude(-13)