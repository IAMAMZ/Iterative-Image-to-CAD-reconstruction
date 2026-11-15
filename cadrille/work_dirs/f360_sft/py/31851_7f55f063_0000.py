import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-17,0))
w1=cq.Workplane('ZX',origin=(0,-8,0))
r=w0.sketch().push([(-75,0)]).circle(25).circle(18,mode='s').push([(65,0)]).circle(35).circle(18,mode='s').finalize().extrude(34).union(w1.sketch().segment((-62,-26),(50,-34)).segment((55,26)).segment((-57,34)).close().assemble().finalize().extrude(13))