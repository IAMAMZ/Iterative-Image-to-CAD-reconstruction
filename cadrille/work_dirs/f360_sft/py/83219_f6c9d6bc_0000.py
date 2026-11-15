import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-37))
r=w0.sketch().segment((-87,-50),(0,-100)).segment((87,-50)).segment((87,50)).segment((0,100)).segment((-87,50)).close().assemble().circle(66,mode='s').finalize().extrude(74)