import cadquery as cq
w0=cq.Workplane('YZ',origin=(13,0,0))
w1=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().push([(0,-82)]).circle(18).circle(15,mode='s').finalize().extrude(-27).union(w1.sketch().segment((-7,-71),(7,-71)).segment((7,76)).arc((1,100),(-7,77)).close().assemble().push([(0,87)]).circle(9,mode='s').finalize().extrude(-14))