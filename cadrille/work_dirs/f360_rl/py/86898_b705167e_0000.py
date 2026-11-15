import cadquery as cq
w0=cq.Workplane('YZ',origin=(9,0,0))
r=w0.sketch().arc((-100,-50),(-5,-19),(100,33.5)).segment((100,50)).segment((-10,50)).segment((-100,50)).close().assemble().finalize().extrude(-16.5)