import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-2,0))
r=w0.sketch().segment((-5.5,-94),(-4,-100)).segment((5.5,-98)).segment((5.5,94)).arc((0,100),(-5.5,94)).close().assemble().push([(0,-94)]).circle(4).push([(0,94)]).circle(3.5).finalize().extrude(4.5)