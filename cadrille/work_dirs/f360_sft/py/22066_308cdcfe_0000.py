import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-24))
w1=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((1,-20),(19,-20)).segment((19,-1)).arc((25,10),(19,21)).segment((19,36)).segment((1,36)).segment((1,21)).arc((-5,10),(1,-1)).close().assemble().push([(10,10)]).circle(10,mode='s').finalize().extrude(53).union(w1.sketch().segment((-36,-50),(-30,-50)).segment((-30,50)).segment((-36,50)).segment((-36,-39)).segment((-34,-39)).segment((-34,-41)).segment((-36,-41)).close().assemble().finalize().extrude(-200))