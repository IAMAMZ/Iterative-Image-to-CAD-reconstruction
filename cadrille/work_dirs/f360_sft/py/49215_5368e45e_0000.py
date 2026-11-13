import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,28))
r=w0.sketch().push([(-75,-67)]).circle(10).push([(-75,70)]).circle(10).push([(81,-67)]).circle(10).push([(80,71)]).circle(9).finalize().extrude(-76).union(w0.workplane(offset=20/2).box(200,166,20))