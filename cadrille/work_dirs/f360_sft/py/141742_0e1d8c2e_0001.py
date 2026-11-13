import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
w1=cq.Workplane('YZ',origin=(-57,0,0))
r=w0.sketch().segment((-11,-57),(1,-57)).segment((1,-34)).segment((-7,-34)).segment((-7,-28)).segment((1,-28)).segment((1,1)).segment((-11,5)).close().assemble().reset().face(w0.sketch().segment((-11,2),(1,-2)).segment((1,57)).segment((-11,57)).close().assemble()).finalize().extrude(200).union(w1.workplane(offset=115/2).moveTo(88,0).cylinder(115,5))