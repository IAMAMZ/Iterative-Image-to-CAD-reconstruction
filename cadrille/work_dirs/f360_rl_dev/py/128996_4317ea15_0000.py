import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,9,0))
r=w0.sketch().segment((-100,-37),(100,-36.5)).segment((100,37)).segment((91,37)).segment((91,0)).segment((-90,0)).segment((-90,37)).segment((-100,37)).close().assemble().finalize().extrude(-18.5)