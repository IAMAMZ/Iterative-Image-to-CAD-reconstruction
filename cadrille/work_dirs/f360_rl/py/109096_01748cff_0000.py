import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,14))
w1=cq.Workplane('YZ',origin=(13,0,0))
r=w0.sketch().segment((-34,-2),(34,-2)).segment((34,67)).arc((0,100),(-33.5,71)).segment((-34,67)).close().assemble().push([(0,65)]).circle(16.5,mode='s').finalize().extrude(19).union(w1.sketch().segment((-67,-33),(1,-33)).segment((1,33)).segment((-67,33)).arc((-100,0),(-67,-33)).assemble().push([(-65,0)]).circle(17,mode='s').finalize().extrude(-26))