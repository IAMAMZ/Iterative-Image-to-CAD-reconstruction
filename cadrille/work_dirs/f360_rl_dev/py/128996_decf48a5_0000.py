import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,20,0))
r=w0.sketch().segment((-49,-100),(-33,-100)).segment((-33,59)).arc((0,83),(33,59)).segment((33,-100)).segment((49,-100)).segment((49,52)).arc((0,100),(-49,52)).close().assemble().push([(40,-97)]).rect(4,2).finalize().extrude(-39)