import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-1))
w1=cq.Workplane('ZX',origin=(0,-34,0))
r=w0.sketch().push([(-69,0)]).circle(10).push([(-69.5,0)]).rect(13,10,mode='s').finalize().extrude(45).union(w0.sketch().push([(0,-0.5)]).rect(86,67).push([(0,0)]).circle(17,mode='s').finalize().extrude(87)).union(w1.sketch().segment((-86,-100),(0,-100)).segment((0,-80)).arc((18,-74),(0,-68)).segment((0,-43)).segment((86,-43)).segment((86,43)).segment((14,43)).arc((7,50),(0,56)).segment((0,100)).segment((-86,100)).close().assemble().finalize().extrude(68))