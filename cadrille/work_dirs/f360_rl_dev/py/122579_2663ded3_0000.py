import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,21))
r=w0.sketch().arc((-100,62),(-20,27),(71,-79)).segment((100,10)).segment((-19,75)).arc((-40,77),(-59,73)).close().assemble().finalize().extrude(-42)