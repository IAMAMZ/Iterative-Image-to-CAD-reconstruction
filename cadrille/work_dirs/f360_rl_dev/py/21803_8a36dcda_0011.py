import cadquery as cq
w0=cq.Workplane('YZ',origin=(-1,0,0))
r=w0.sketch().segment((-88,-50),(0,-100)).segment((88,-50)).segment((87,50)).segment((0,100)).segment((-87.5,50)).close().assemble().circle(73,mode='s').finalize().extrude(1.5)