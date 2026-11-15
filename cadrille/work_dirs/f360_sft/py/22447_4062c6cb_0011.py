import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,31,0))
r=w0.workplane(offset=-75/2).cylinder(75,63).union(w0.workplane(offset=13/2).cylinder(13,100))