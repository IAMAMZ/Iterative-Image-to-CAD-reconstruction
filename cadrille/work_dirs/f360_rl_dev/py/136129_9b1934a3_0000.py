import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-45,0))
r=w0.workplane(offset=80/2).box(100,200,80).union(w0.sketch().segment((-49,-100),(50,-100)).segment((49,100)).segment((-49,100)).close().assemble().finalize().extrude(81)).union(w0.sketch().push([(-22,-70)]).circle(14.5).push([(27,66)]).circle(12.5).finalize().extrude(90))