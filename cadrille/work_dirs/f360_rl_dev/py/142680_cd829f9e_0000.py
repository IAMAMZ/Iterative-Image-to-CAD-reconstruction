import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,10))
r=w0.sketch().segment((-69,-100),(69,-100)).segment((69,31)).segment((0,100)).segment((-69,31)).close().assemble().push([(0,26)]).circle(17.5,mode='s').push([(0,-5)]).circle(2).finalize().extrude(-19)