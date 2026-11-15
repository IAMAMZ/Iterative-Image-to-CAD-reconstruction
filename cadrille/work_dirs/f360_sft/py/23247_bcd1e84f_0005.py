import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-63,0))
w1=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().arc((-70,79),(-62,57),(-62,34)).segment((-61,34)).segment((-61,-15)).arc((-62,-40),(-42,-54)).segment((-42,-55)).segment((99,-90)).segment((100,-57)).arc((35,-40),(-27,-24)).segment((-27,-23)).arc((-28,33),(-36,90)).close().assemble().finalize().extrude(126).union(w1.sketch().segment((-10,-9),(62,-9)).segment((62,9)).segment((-10,9)).segment((-10,7)).arc((-16,-2),(-10,-11)).close().assemble().finalize().extrude(110))