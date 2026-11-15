import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-2,0))
r=w0.sketch().segment((-57,-100),(54.5,-100)).segment((55,-56)).segment((57,-56)).segment((57,100)).segment((-57,100)).close().assemble().finalize().extrude(4.5)