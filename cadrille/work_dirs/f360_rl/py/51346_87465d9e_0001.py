import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-1))
r=w0.sketch().segment((-100,-20),(-59,-41)).arc((0,-47),(79,-25)).segment((100,-20)).segment((100,20)).segment((59,41)).arc((-10,47),(-100,20)).close().assemble().finalize().extrude(2.5)