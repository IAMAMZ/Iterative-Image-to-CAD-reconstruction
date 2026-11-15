import cadquery as cq
w0=cq.Workplane('YZ',origin=(-2,0,0))
r=w0.sketch().segment((-100,98),(74,-81)).segment((71,-100)).segment((100,-100)).segment((75,-69)).segment((-99,100)).close().assemble().finalize().extrude(3)