import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-56,0))
r=w0.sketch().segment((-63,-99),(-51,-100)).arc((-4,-55),(37,-100)).segment((48,-100)).segment((63,52)).arc((21,100),(-26,58)).segment((-31,58)).close().assemble().push([(19,56)]).circle(37,mode='s').finalize().extrude(112)