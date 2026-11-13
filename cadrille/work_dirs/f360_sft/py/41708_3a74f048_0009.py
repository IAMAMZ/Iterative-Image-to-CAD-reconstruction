import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-5,0))
r=w0.sketch().segment((-100,-11),(100,-1)).segment((100,1)).segment((-79,11)).segment((-79,10)).segment((-100,10)).close().assemble().finalize().extrude(9)