import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).moveTo(3.5,0).box(17.5,22,200).union(w0.workplane(offset=-192/2).moveTo(0,7.5).box(27.5,5.5,192)).union(w0.workplane(offset=-2/2).moveTo(9.5,0.5).box(1.5,1.5,1))