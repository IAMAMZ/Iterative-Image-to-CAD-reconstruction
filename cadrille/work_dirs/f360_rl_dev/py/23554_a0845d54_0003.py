import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().segment((-86.5,-50),(0,-100)).segment((86.5,-50)).segment((86.5,50)).segment((0,100)).segment((-86.5,50)).close().assemble().circle(76.5,mode='s').finalize().extrude(-9)