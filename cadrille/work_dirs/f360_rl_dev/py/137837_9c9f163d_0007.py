import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-28,0),(-4.5,0)).segment((-4,-18.5)).segment((28,-18)).segment((28,17.5)).segment((-28,17)).close().assemble().finalize().extrude(-200)