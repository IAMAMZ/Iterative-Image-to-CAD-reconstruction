import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-3,0))
r=w0.sketch().arc((-20,-81),(10,-97),(13,-63)).arc((0,5),(20,68)).arc((5,99),(-20,77)).close().assemble().finalize().extrude(6)