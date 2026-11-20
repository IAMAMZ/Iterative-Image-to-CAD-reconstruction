import cadquery as cq
w0=cq.Workplane('YZ',origin=(-1,0,0))
r=w0.sketch().segment((-100,-8),(-36,-8)).segment((-36,-66)).segment((100,-66)).segment((100,66)).segment((-36,65.5)).segment((-36,8)).segment((-100,8)).close().assemble().finalize().extrude(3)