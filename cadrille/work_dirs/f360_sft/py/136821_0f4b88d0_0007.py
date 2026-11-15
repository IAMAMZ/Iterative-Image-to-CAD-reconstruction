import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-31,-97),(-30,-97)).arc((-10,-99),(10,-99)).segment((31,-97)).segment((31,97)).segment((30,97)).arc((0,99),(-30,97)).segment((-31,97)).close().assemble().push([(0,-57)]).circle(12,mode='s').push([(0,57)]).circle(12,mode='s').finalize().extrude(28)