import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-18,-8),(-12,2)).arc((3,3),(15,-8)).segment((18,-6)).arc((0,8),(-18,-7)).close().assemble().finalize().extrude(-200)