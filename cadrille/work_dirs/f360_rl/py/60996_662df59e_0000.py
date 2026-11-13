import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-35,-55),(23.5,-50)).segment((35,31)).segment((-17,55)).arc((-22,1),(-35,-54)).close().assemble().finalize().extrude(-200)