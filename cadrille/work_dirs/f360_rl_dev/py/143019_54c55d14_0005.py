import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().rect(25,200).finalize().extrude(-200).union(w0.workplane(offset=-2/2).box(15.5,192.5,2))