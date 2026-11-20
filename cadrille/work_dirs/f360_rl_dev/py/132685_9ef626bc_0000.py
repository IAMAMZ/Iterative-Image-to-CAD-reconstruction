import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).moveTo(0,-21).box(171.5,51.5,200).union(w0.workplane(offset=-150/2).moveTo(0,0).box(74,95,150)).union(w0.workplane(offset=-139/2).moveTo(0.5,0.5).box(7.5,8.5,13))