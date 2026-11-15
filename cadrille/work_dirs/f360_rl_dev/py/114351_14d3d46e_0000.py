import cadquery as cq
w0=cq.Workplane('YZ',origin=(58,0,0))
w1=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().push([(-99,-20)]).rect(2,33).push([(95,-0)]).rect(10,75).finalize().extrude(-116).union(w1.workplane(offset=-198/2).moveTo(-8,0).box(16,90,198)).union(w1.workplane(offset=-6/2).moveTo(0,56.5).box(1.5,1.5,1))