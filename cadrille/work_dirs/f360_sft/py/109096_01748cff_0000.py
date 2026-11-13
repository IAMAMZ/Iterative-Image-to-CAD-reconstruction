import cadquery as cq
w0=cq.Workplane('YZ',origin=(-14,0,0))
w1=cq.Workplane('XY',origin=(0,0,12))
r=w0.sketch().segment((-67,-34),(-67,-33)).segment((-1,-33)).segment((-1,32)).segment((-67,32)).segment((-67,34)).arc((-100,0),(-67,-34)).assemble().push([(-67,0)]).circle(17,mode='s').finalize().extrude(28).union(w1.sketch().segment((-33,0),(33,0)).segment((33,64)).arc((1,100),(-33,68)).close().assemble().push([(0,67)]).circle(17,mode='s').finalize().extrude(21))