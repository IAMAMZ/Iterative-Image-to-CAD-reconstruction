import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1.5,0))
r=w0.sketch().segment((-100,-7.5),(100,-7.5)).segment((100,1)).segment((-8,5)).segment((-94,6.5)).segment((-100,0)).close().assemble().finalize().extrude(3.5)