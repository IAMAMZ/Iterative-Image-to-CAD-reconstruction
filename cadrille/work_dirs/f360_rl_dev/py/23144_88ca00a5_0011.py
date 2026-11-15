import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-4,6),(-3,-7)).segment((4,-7)).segment((4,3)).segment((0,6.5)).close().assemble().finalize().extrude(-200)