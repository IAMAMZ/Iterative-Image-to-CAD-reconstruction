import cadquery as cq
w0=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().arc((-40,100),(-16,87),(2,68)).segment((2,-76)).segment((-2,-76)).segment((-2,-78)).segment((40,-100)).arc((16,-87),(-2,-68)).segment((-2,76)).segment((2,76)).segment((2,78)).close().assemble().finalize().extrude(-15)