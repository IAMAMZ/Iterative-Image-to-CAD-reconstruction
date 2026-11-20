import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-2,-2),(3,-2)).segment((3,3)).segment((2,2)).segment((2,-1)).segment((-2,-1.5)).close().assemble().finalize().extrude(-200)