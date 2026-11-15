import cadquery as cq
w0=cq.Workplane('YZ',origin=(-22,0,0))
r=w0.sketch().segment((-87,-50),(1,-100)).segment((87,-50)).segment((87,50)).segment((0,100)).segment((-87,50)).close().assemble().finalize().extrude(44)