import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,10,0))
r=w0.sketch().segment((-100,-58),(100,58)).segment((-100,58)).close().assemble().finalize().extrude(-19)