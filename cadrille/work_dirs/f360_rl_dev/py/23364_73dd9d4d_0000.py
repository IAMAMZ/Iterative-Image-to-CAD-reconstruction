import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-34.5,-56),(29.5,-56)).segment((34,-49)).segment((34,56)).segment((-34.5,55.5)).close().assemble().push([(-25,45)]).circle(3).finalize().extrude(-200).union(w0.workplane(offset=-22/2).moveTo(-0.5,0).box(9.5,110.5,22)).union(w0.workplane(offset=-9/2).box(1.5,11.5,8))