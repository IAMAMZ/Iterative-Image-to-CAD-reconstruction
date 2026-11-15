import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,2))
r=w0.sketch().push([(-91,0)]).circle(9.5).circle(6,mode='s').reset().face(w0.sketch().segment((-82,-7),(31,-9)).segment((100,-10)).segment((100,10)).segment((31.5,8.5)).segment((-82,7.5)).close().assemble()).push([(68,-0)]).circle(7.5,mode='s').finalize().extrude(-5.5)