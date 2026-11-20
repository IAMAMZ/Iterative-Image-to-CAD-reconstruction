import cadquery as cq
w0=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().segment((-100,-75),(100,-75)).segment((100,75)).segment((-10,75.5)).segment((-100,75)).close().assemble().finalize().extrude(-14)