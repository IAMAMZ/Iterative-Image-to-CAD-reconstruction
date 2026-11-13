import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,2))
r=w0.sketch().segment((-86,-98),(-4,-98)).segment((-4,-100)).segment((86,-100)).segment((86,100)).segment((-4,100)).segment((-4,-12)).segment((-86,-12)).close().assemble().finalize().extrude(-3)