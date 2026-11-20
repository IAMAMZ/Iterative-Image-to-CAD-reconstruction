import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,6))
r=w0.sketch().segment((-61,-100),(61.5,-100)).segment((61.5,100)).segment((-1,100)).segment((-61,100)).close().assemble().push([(1,0)]).rect(16.5,50,mode='s').push([(0,-63)]).circle(3.5,mode='s').push([(0,50)]).circle(2.5).finalize().extrude(-11)