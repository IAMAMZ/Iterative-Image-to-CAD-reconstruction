import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,31))
w1=cq.Workplane('YZ',origin=(80,0,0))
r=w0.sketch().segment((-100,-86),(89,-89)).segment((100,-86)).segment((100,8)).arc((0,100),(-100,0)).close().assemble().circle(62.5,mode='s').finalize().extrude(-62.5).union(w1.workplane(offset=-180/2).moveTo(-97,0.5).box(6,39.5,180))