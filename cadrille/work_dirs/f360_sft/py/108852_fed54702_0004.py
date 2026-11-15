import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().arc((-5,3),(4,-4),(-2,6)).arc((-2,3),(-5,3)).assemble().finalize().extrude(200)