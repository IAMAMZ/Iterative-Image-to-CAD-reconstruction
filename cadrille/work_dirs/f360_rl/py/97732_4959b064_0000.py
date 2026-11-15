import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,19))
r=w0.sketch().segment((-83,72),(-36,-75)).segment((-35.5,-100)).segment((35,-100)).segment((35,-74)).segment((83,72)).segment((83,100)).segment((-19.5,100)).segment((-83,100)).close().assemble().finalize().extrude(-38.5)