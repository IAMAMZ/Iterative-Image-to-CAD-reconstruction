import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).moveTo(0,0).box(16,56,200).union(w0.workplane(offset=-199/2).box(15.5,9.5,19)).union(w0.workplane(offset=-199/2).box(15.5,1.5,1))