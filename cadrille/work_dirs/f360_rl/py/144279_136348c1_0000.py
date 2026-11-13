import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-36,0))
w1=cq.Workplane('ZX',origin=(0,-53,0))
r=w0.sketch().segment((-20,-100),(20,-100)).segment((20,-50)).segment((20,10)).segment((20,91)).segment((20,100)).segment((-20,100)).segment((-20,50)).close().assemble().push([(0,-79)]).circle(10.5,mode='s').finalize().extrude(20.5).union(w0.sketch().push([(0,-40)]).rect(40,22.5).push([(0,40)]).rect(40,22).finalize().extrude(89)).union(w1.workplane(offset=6/2).moveTo(0,-49.5).box(2.5,3.5,2))