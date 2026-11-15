import cadquery as cq
w0=cq.Workplane('YZ',origin=(26,0,0))
w1=cq.Workplane('XY',origin=(0,0,35))
r=w0.sketch().segment((-36,-29),(-29,-29)).segment((-29,-35)).segment((-24,-35)).segment((-24,35)).segment((-36,35)).close().assemble().push([(-31.5,0)]).rect(5,10,mode='s').finalize().extrude(-126).union(w1.sketch().segment((-100,-36),(24,-36)).segment((24,-37)).segment((100,-37)).segment((100,37)).segment((24,37)).segment((24,11)).segment((-78,11)).segment((-78,36)).segment((-100,36)).close().assemble().finalize().extrude(-72))