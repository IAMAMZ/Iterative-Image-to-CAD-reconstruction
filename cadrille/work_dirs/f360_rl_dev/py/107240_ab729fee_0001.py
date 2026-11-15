import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,3))
r=w0.sketch().segment((-100,-13),(87,-13)).segment((88,-7)).segment((100,-7)).segment((100,7)).segment((87,7)).segment((86.5,13)).segment((-100,13.5)).close().assemble().finalize().extrude(-6)