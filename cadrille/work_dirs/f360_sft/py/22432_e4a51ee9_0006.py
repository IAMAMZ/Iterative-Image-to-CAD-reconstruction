import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-69))
w1=cq.Workplane('ZX',origin=(0,-33,0))
r=w0.sketch().segment((-100,1),(-50,-86)).segment((50,-86)).segment((100,0)).segment((50,86)).close().assemble().circle(21,mode='s').push([(38,79)]).circle(6,mode='s').finalize().extrude(138).union(w1.sketch().push([(0,-1)]).rect(136,94).push([(-52,-34)]).circle(6,mode='s').push([(0,-1)]).circle(42,mode='s').finalize().extrude(120))