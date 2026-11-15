import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-100,-87),(100,-87)).segment((0,87)).close().assemble().finalize().extrude(-200)