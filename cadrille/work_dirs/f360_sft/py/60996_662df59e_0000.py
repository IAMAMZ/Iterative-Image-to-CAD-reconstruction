import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((-36,-55),(23,-50)).segment((36,30)).segment((-18,55)).arc((-20,-1),(-36,-55)).assemble().finalize().extrude(200)