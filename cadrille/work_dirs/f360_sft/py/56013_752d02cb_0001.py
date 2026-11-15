import cadquery as cq
w0=cq.Workplane('YZ',origin=(-4,0,0))
r=w0.sketch().segment((-10,-95),(-6,-95)).segment((-6,-100)).segment((6,-100)).segment((6,-95)).segment((10,-95)).segment((10,95)).segment((6,95)).segment((6,100)).segment((-6,100)).segment((-6,95)).segment((-10,95)).close().assemble().push([(1,-91)]).circle(4,mode='s').finalize().extrude(8)