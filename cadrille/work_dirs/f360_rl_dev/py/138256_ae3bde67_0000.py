import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,17,0))
r=w0.sketch().segment((-71,-100),(31,-100)).arc((65,-46),(71,7)).arc((65,46),(33,97)).segment((31,100)).segment((-71,100)).close().assemble().finalize().extrude(-33.5)