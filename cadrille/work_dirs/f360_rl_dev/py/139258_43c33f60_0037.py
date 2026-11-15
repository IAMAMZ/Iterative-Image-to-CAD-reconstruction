import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,13,0))
r=w0.workplane(offset=-26/2).box(200,200,26).union(w0.workplane(offset=-11/2).box(17.5,17.5,11)).union(w0.workplane(offset=-7/2).box(17.5,1.5,6))