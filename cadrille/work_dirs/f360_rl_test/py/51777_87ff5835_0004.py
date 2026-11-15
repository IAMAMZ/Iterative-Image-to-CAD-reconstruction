import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,93))
r=w0.sketch().segment((-100,-4),(-1,-4)).segment((-1,-3)).segment((10,-3)).segment((100,-4)).segment((100,4)).segment((-100,4)).close().assemble().finalize().extrude(-186)