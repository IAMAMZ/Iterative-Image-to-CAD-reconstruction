import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-10,0))
r=w0.sketch().segment((-31,-71),(-30,-71)).arc((0,-100),(30,-71)).segment((31,-71)).segment((31,71)).segment((30,71)).arc((0,100),(-30,71)).segment((-31,71)).close().assemble().push([(0,-69)]).circle(10,mode='s').push([(0,69)]).circle(10,mode='s').finalize().extrude(20)