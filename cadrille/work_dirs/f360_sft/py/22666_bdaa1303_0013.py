import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-13,0))
r=w0.sketch().segment((-87,-50),(0,-100)).segment((10,-84)).segment((87,-50)).segment((87,50)).segment((0,100)).segment((-10,84)).segment((-87,50)).close().assemble().circle(63,mode='s').finalize().extrude(26)