import cadquery as cq
w0=cq.Workplane('YZ',origin=(8,0,0))
r=w0.sketch().arc((-100,-50),(2,-16),(100,33)).segment((100,50)).segment((-100,50)).close().assemble().finalize().extrude(-16)