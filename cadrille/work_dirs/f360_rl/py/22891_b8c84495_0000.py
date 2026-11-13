import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,34,0))
r=w0.sketch().arc((-100,-34),(100,0),(-100,34)).arc((-92,1),(-100,-34)).assemble().push([(17,0)]).circle(74.5,mode='s').finalize().extrude(-66.5)