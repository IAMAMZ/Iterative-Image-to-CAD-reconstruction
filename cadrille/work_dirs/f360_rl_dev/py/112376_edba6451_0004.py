import cadquery as cq
w0=cq.Workplane('YZ',origin=(3,0,0))
r=w0.sketch().arc((-10,-89),(0,-100),(10,-89)).segment((10,89)).arc((0,100),(-10,89)).close().assemble().push([(0,-87)]).circle(4,mode='s').push([(0,47)]).circle(4.5,mode='s').push([(0,-45)]).circle(4.5,mode='s').push([(0,87)]).circle(4,mode='s').finalize().extrude(-4.5)