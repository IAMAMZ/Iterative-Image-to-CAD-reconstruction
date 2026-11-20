import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,20,0))
r=w0.sketch().arc((-100,-3),(-45,-76),(49,-35)).segment((99,-32.5)).segment((100,32.5)).segment((50,34)).arc((-39,77),(-100,2)).close().assemble().push([(-21,0)]).circle(35.5,mode='s').finalize().extrude(-40)