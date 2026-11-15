import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-14,0))
r=w0.sketch().push([(0,0)]).rect(31,200).push([(6,-70)]).circle(4,mode='s').push([(5,73)]).circle(4).finalize().extrude(8).union(w0.workplane(offset=27/2).moveTo(-12.5,0).box(7,200,27))