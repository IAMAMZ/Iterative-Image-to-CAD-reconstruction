import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,19))
r=w0.sketch().segment((-93,-9),(94,-9)).arc((100,2),(94,9)).segment((-93.5,9)).arc((-100,0),(-93,-9)).assemble().push([(0,-0)]).rect(182.5,10,mode='s').push([(-89,0)]).circle(4,mode='s').push([(90,0)]).circle(4,mode='s').finalize().extrude(-37.5)