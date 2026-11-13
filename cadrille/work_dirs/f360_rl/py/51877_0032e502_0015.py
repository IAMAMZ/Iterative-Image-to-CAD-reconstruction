import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-100,-83),(100,-83)).segment((100,83)).segment((-66.5,83)).close().assemble().finalize().extrude(-200)