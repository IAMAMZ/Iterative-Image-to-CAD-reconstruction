import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
w1=cq.Workplane('YZ',origin=(-4,0,0))
r=w0.sketch().segment((-6,-36),(69,-36)).arc((100,0),(69,36)).segment((-6,36)).close().assemble().push([(65,0)]).circle(16.5,mode='s').finalize().extrude(-42).union(w0.sketch().segment((-9,-36),(79,-36)).arc((100,0),(79,36)).segment((-9,36)).close().assemble().push([(65,0)]).circle(17.5,mode='s').finalize().extrude(28)).union(w1.sketch().push([(0,0)]).circle(23).circle(13.5,mode='s').finalize().extrude(-96)).union(w1.workplane(offset=1/2).moveTo(0,31.5).box(1.5,6.5,1))