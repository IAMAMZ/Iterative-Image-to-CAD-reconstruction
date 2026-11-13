import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-34,0))
r=w0.sketch().segment((0,-62),(100,-62)).segment((100,62)).segment((0,62)).close().assemble().push([(50,0)]).rect(77.5,115.5,mode='s').finalize().extrude(40).union(w0.sketch().push([(-38,0)]).rect(124,124).finalize().extrude(68.5)).union(w0.workplane(offset=68/2).moveTo(97.5,0.5).box(1,1.5,68))