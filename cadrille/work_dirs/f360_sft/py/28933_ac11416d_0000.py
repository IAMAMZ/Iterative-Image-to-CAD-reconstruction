import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,17))
r=w0.sketch().arc((-21,73),(-1,-100),(23,72)).arc((21,84),(13,94)).segment((12,94)).arc((11,95),(10,95)).segment((10,96)).arc((-7,98),(-14,82)).arc((-18,78),(-21,73)).assemble().push([(0,-13)]).circle(56,mode='s').finalize().extrude(-34)