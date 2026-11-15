import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,67))
r=w0.workplane(offset=-167/2).moveTo(0,0).box(182,95,167).union(w0.sketch().push([(-35,0)]).circle(48).push([(10,0)]).circle(18.5).finalize().extrude(33)).union(w0.workplane(offset=33/2).moveTo(87,42.5).box(2.5,6.5,33))