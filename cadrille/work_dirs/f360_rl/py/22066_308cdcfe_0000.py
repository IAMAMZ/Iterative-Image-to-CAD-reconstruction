import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,50))
w1=cq.Workplane('ZX',origin=(0,35,0))
r=w0.sketch().push([(0,-33)]).rect(200,5).finalize().extrude(-100).union(w0.workplane(offset=-74/2).moveTo(9,22).box(17,22.5,74)).union(w1.workplane(offset=-19/2).moveTo(4,10.5).box(1.5,1.5,1))