import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().arc((-13,6),(-10,-9),(5,-13)).arc((7,-10),(10,-10)).arc((12,6),(-3,13)).arc((-5,7),(-13,6)).assemble().finalize().extrude(6).union(w0.workplane(offset=200/2).cylinder(200,9))