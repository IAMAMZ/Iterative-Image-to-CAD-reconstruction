import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-5,-6),(5,-6)).segment((5,6)).segment((-5,6)).segment((-5,3)).segment((2,3)).segment((2,-2)).segment((-5,-2)).close().assemble().finalize().extrude(-200)