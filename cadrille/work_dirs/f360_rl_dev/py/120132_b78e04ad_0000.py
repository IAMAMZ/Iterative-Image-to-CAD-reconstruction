import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.workplane(offset=12/2).cylinder(12,100).union(w0.sketch().segment((-35,-95),(35,-95)).segment((35,-90)).arc((57,-1),(35,89)).segment((35,95)).segment((-35,95)).segment((-35,89)).arc((-97,-1),(-35,-90)).close().assemble().circle(49.5,mode='s').finalize().extrude(17))