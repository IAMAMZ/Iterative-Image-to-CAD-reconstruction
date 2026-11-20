import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.workplane(offset=-200/2).moveTo(0,-0).box(10,36.5,200).union(w0.workplane(offset=-19/2).box(9.5,1.5,1))