import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,11,0))
r=w0.sketch().arc((-31,-69),(0,-100),(31,-69)).segment((31,69)).arc((0,100),(-31,69)).close().assemble().push([(0,-69)]).circle(10,mode='s').push([(0,69)]).circle(10,mode='s').finalize().extrude(-20)