import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-70))
w1=cq.Workplane('YZ',origin=(71,0,0))
r=w0.sketch().segment((-36,-58),(98,-58)).segment((98,58)).segment((-36,58)).segment((-36,57)).arc((-100,0),(-36,-57)).close().assemble().push([(-45,0)]).circle(35,mode='s').finalize().extrude(-30).union(w1.sketch().push([(0,35)]).circle(65).circle(37,mode='s').finalize().extrude(29))