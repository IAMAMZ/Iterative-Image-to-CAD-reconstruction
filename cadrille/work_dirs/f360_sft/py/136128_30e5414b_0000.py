import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-59))
w1=cq.Workplane('XY',origin=(0,0,-42))
r=w0.sketch().arc((-35,53),(-95,-23),(1,-24)).arc((38,11),(100,18)).segment((100,53)).close().assemble().finalize().extrude(118).union(w1.workplane(offset=84/2).moveTo(-24,34.5).box(18,37,84))