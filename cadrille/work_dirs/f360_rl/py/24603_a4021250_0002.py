import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).box(1,56,200).union(w0.workplane(offset=-1/2).box(1,1,1)).union(w0.workplane(offset=-1/2).box(1,1.5,1))