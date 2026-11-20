import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,9,0))
w1=cq.Workplane('XY',origin=(0,0,77))
r=w0.sketch().segment((-93,-9),(-76,-9)).segment((-76,9)).segment((-93,9)).arc((-100,0),(-93,-9)).assemble().push([(-88,0)]).circle(4.5,mode='s').finalize().extrude(-19).union(w0.workplane(offset=-6/2).moveTo(90.5,0).box(19.5,6.5,6)).union(w1.workplane(offset=-153/2).moveTo(0,0).cylinder(153,6.5)).union(w1.workplane(offset=-10/2).moveTo(0.5,0.5).box(1.5,1,6.5))