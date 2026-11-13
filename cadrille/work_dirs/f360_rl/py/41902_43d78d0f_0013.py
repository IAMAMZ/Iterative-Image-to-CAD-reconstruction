import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,4,0))
r=w0.sketch().arc((-21,-80),(2,-100),(21,-80)).arc((0,-10),(18.5,69)).segment((21,77)).arc((2,100),(-20,80)).segment((-21,70)).close().assemble().finalize().extrude(-7)