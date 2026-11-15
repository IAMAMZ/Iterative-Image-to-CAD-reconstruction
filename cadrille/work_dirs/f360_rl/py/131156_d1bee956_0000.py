import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().arc((-34,-63),(0,-100),(34,-63)).segment((34,63)).arc((0,100),(-34,63)).close().assemble().push([(0,67)]).circle(20,mode='s').push([(0,-67)]).circle(20,mode='s').push([(0,0)]).rect(28.5,53.5,mode='s').finalize().extrude(2)