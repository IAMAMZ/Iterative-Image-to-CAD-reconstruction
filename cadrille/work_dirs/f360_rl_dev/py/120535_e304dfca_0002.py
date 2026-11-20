import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,16.5))
r=w0.sketch().segment((-76,-100),(76.5,-100)).segment((76.5,25)).arc((0,100),(-76,27)).close().assemble().finalize().extrude(-33)