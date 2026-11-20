import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).moveTo(0,0).box(15,29.5,200).union(w0.workplane(offset=-199/2).box(15.5,1.5,19)).union(w0.workplane(offset=-199/2).box(13.5,1.5,1))