import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().arc((-37,22),(-40,-1),(-31,-23)).arc((-3,-100),(30,-25)).arc((40,-4),(38,20)).arc((1,100),(-37,22)).assemble().push([(0,11)]).circle(31,mode='s').push([(0,-60)]).circle(31,mode='s').finalize().extrude(20)