import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,73,0))
w1=cq.Workplane('ZX',origin=(0,39,0))
r=w0.workplane(offset=-146/2).moveTo(0,86).box(118,28,146).union(w1.sketch().arc((-29,11),(0,-100),(29,11)).segment((29,80)).segment((-29,80)).close().assemble().push([(0,-41)]).circle(31,mode='s').finalize().extrude(-78))