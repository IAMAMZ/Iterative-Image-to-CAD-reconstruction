import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
w1=cq.Workplane('ZX',origin=(0,17,0))
r=w0.sketch().segment((-55,-25),(39,-34)).segment((46,31)).segment((-50,26)).close().assemble().finalize().extrude(-14).union(w1.sketch().push([(-74,0)]).circle(25.5).circle(18,mode='s').push([(65,0)]).circle(35).circle(18,mode='s').finalize().extrude(-34))