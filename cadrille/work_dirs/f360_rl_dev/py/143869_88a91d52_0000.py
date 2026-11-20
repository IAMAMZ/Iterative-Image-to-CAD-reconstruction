import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-22,-43),(22,-31)).segment((22,32)).segment((-22,43)).close().assemble().finalize().extrude(-200)