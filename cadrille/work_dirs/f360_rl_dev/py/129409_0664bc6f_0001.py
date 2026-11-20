import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).moveTo(0,-0).box(8,80,200).union(w0.workplane(offset=-19/2).box(7.5,6.5,19)).union(w0.workplane(offset=-19/2).box(7.5,1.5,1))