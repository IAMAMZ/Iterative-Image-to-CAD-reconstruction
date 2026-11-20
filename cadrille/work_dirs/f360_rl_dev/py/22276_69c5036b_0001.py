import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,23,0))
r=w0.sketch().segment((-100,-21),(22,-21)).segment((22,-56.5)).segment((100,-56)).segment((100,56)).segment((-10,56)).segment((-100,56)).close().assemble().push([(-61,17)]).circle(14,mode='s').push([(62,16)]).circle(14,mode='s').finalize().extrude(-45.5)