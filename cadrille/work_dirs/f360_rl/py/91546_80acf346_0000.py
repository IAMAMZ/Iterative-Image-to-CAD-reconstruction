import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-43,-50),(43,0)).segment((-43,50)).close().assemble().finalize().extrude(-200)