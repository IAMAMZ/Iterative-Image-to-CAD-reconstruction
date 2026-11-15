import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().segment((-87,-14),(79,-13.5)).segment((82,-33)).segment((100,-25.5)).segment((100,25.5)).segment((82,33)).segment((79,13.5)).segment((-87,13.5)).arc((-100,1),(-87,-14)).assemble().push([(-62.5,-0)]).rect(43.5,13.5,mode='s').push([(87,-18)]).circle(5.5,mode='s').push([(87,19)]).circle(6.5,mode='s').finalize().extrude(-12)