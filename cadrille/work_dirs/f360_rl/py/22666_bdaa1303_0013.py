import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,13,0))
r=w0.sketch().segment((-86,-50),(0,-100)).segment((86,-50)).segment((85.5,50)).segment((0,100)).segment((-86,50)).close().assemble().circle(63.5,mode='s').finalize().extrude(-26)