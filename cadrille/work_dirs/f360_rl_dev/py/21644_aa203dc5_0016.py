import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,17))
r=w0.sketch().segment((-100,-12),(100,-12.5)).segment((100,4)).segment((25,4)).segment((25,14)).segment((-26,14)).segment((-26,4)).segment((-100,4)).close().assemble().finalize().extrude(-33.5)