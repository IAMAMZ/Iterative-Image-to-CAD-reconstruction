import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,37))
r=w0.sketch().segment((-100,28),(-59,-28)).segment((58,-28)).segment((100,28)).segment((-9.5,28)).close().assemble().finalize().extrude(-73)