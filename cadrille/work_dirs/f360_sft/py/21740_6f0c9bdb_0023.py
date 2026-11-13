import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-3,-100),(-3,-91)).arc((-29,85),(30,-86)).segment((30,-100)).arc((0,100),(-3,-100)).assemble().finalize().extrude(10)