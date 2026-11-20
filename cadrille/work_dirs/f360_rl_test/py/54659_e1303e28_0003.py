import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,10))
r=w0.sketch().segment((-19,-95),(-14,-100)).segment((-8,-95)).segment((0,41)).segment((19,49)).segment((1,100)).segment((-16,79)).segment((-18,66)).segment((-18,57)).close().assemble().finalize().extrude(-20)