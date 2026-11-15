import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-61,0))
w1=cq.Workplane('XY',origin=(0,0,81))
r=w0.sketch().rect(162,162).push([(-61,-60)]).circle(4,mode='s').push([(-58,59)]).circle(4,mode='s').push([(59,-59)]).circle(4,mode='s').finalize().extrude(-39).union(w0.workplane(offset=161/2).moveTo(78.5,0).box(5,92,161)).union(w1.sketch().segment((-45,-63),(45,-63)).segment((45,-14)).segment((26,-14)).segment((26,-58)).segment((-26,-58)).segment((-26,-14)).segment((-45,-14)).close().assemble().finalize().extrude(-163))