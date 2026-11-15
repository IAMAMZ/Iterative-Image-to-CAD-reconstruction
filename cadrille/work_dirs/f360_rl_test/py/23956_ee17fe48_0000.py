import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,0,0))
w1=cq.Workplane('YZ',origin=(31,0,0))
r=w0.sketch().push([(0,0)]).circle(29.5).circle(23,mode='s').finalize().extrude(-92).union(w1.sketch().segment((4,-100),(76,-100)).arc((88,-93),(92,-81)).segment((92,86.5)).arc((86,96),(76,100)).segment((4.5,100)).close().assemble().finalize().extrude(-61.5)).union(w1.workplane(offset=-10/2).moveTo(87.5,96.5).box(7,1.5,6))