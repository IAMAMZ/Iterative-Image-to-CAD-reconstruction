import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-27,0))
r=w0.sketch().arc((-22,-83),(1,-100),(22,-80)).arc((45,-28),(31,25)).arc((3,100),(-22,24)).arc((-45,-29),(-22,-83)).assemble().push([(0,-72)]).circle(10,mode='s').push([(2,72)]).circle(10,mode='s').finalize().extrude(23).union(w0.sketch().push([(0,-1)]).circle(48).circle(32,mode='s').finalize().extrude(55))