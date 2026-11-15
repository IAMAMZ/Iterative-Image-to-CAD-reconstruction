import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,44))
r=w0.sketch().segment((-51,-50),(50,-50)).arc((100,0),(50,50)).segment((-51,50)).arc((-100,0),(-51,-50)).assemble().finalize().extrude(-87.5)