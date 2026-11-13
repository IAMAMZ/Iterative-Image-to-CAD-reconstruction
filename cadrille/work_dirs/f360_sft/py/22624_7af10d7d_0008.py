import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
w1=cq.Workplane('YZ',origin=(-8,0,0))
r=w0.sketch().segment((-23,-70),(18,-72)).segment((23,94)).segment((-18,96)).close().assemble().finalize().extrude(12).union(w0.sketch().push([(0,-74)]).circle(26).circle(12,mode='s').push([(2,84)]).circle(10).finalize().extrude(25)).union(w1.sketch().push([(84,-24)]).circle(12).circle(9,mode='s').finalize().extrude(13))