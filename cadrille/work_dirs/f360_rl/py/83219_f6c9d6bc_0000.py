import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,37))
r=w0.sketch().segment((-86.5,-50),(0,-100)).segment((86.5,-50)).segment((86.5,50)).segment((0,100)).segment((-86.5,50)).close().assemble().circle(66.5,mode='s').finalize().extrude(-73)