import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().segment((-13,-28),(13,-28)).segment((13,-10)).segment((-13,-14)).close().assemble().reset().face(w0.sketch().segment((-13,10),(13,14)).segment((13,28)).segment((-13,28)).close().assemble()).finalize().extrude(200)