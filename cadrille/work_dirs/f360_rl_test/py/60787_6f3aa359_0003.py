import cadquery as cq
w0=cq.Workplane('YZ',origin=(81,0,0))
r=w0.workplane(offset=-162/2).moveTo(0,-0).box(2.5,200,162).union(w0.workplane(offset=-10/2).box(2.5,1,9)).union(w0.workplane(offset=-2/2).box(2.5,1.5,1))