import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,44,0))
w1=cq.Workplane('ZX',origin=(0,53,0))
r=w0.sketch().push([(-62,-75)]).circle(10).push([(-63,75)]).circle(10).push([(62,75)]).circle(10).push([(63,-75)]).circle(10).finalize().extrude(-115).union(w1.workplane(offset=18/2).box(174,200,18))