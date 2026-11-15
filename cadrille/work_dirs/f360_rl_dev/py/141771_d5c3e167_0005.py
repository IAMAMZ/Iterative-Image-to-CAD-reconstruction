import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-2))
r=w0.workplane(offset=2/2).box(200,57,2).union(w0.sketch().segment((-100,-28),(100,-28)).segment((100,28.5)).segment((-100,28.5)).close().assemble().finalize().extrude(5))