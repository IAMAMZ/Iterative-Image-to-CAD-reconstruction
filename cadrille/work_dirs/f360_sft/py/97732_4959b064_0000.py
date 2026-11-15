import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,19))
r=w0.sketch().segment((-84,72),(-35,-74)).segment((-35,-100)).segment((35,-100)).segment((35,-74)).segment((84,72)).segment((84,100)).segment((-84,100)).close().assemble().finalize().extrude(-38)