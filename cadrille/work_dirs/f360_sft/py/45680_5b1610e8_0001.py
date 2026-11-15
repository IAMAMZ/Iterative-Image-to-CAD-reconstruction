import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-2,-2),(-2,2)).segment((2,2)).segment((2,-2)).close().assemble().finalize().extrude(-200)