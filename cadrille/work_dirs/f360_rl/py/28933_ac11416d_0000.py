import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,17))
r=w0.sketch().arc((-21,75),(-2,-100),(23,75)).segment((14,100)).segment((-10,100)).segment((-21,81)).close().assemble().push([(0,-12)]).circle(56,mode='s').finalize().extrude(-33.5)