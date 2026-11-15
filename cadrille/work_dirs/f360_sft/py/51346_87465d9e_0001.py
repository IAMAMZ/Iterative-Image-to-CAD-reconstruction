import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-1))
r=w0.sketch().segment((-100,-20),(-96,-20)).arc((-1,-47),(94,-20)).segment((99,-20)).segment((100,20)).segment((96,20)).arc((-1,47),(-94,20)).segment((-99,20)).close().assemble().finalize().extrude(3)