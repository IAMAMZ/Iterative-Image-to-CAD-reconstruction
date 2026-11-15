import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-13,-28),(13,-28)).segment((13,-14.5)).segment((-12,-15)).segment((-13,-16)).close().assemble().reset().face(w0.sketch().segment((-12,14),(13,13)).segment((13,28)).segment((-12.5,28)).close().assemble()).finalize().extrude(-200)