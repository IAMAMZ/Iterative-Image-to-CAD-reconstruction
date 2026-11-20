import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,35,0))
r=w0.workplane(offset=-69/2).box(200,200,69).union(w0.workplane(offset=-29/2).box(186.5,17.5,29))