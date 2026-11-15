import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,56,0))
r=w0.sketch().segment((-63,-100),(-50,-100)).arc((-5,-55),(39,-100)).segment((48.5,-100)).segment((62.5,49)).arc((22,99),(-25,62)).close().assemble().push([(20,56)]).circle(37.5,mode='s').finalize().extrude(-112)