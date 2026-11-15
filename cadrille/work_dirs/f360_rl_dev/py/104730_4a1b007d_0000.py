import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
w1=cq.Workplane('ZX',origin=(0,83,0))
r=w0.sketch().push([(-17,-69)]).circle(22).circle(17,mode='s').push([(-17,68)]).circle(23).circle(17.5,mode='s').finalize().extrude(-200).union(w1.workplane(offset=-97/2).moveTo(12.5,8.5).box(55,85.5,97)).union(w1.workplane(offset=-18/2).moveTo(34.5,4.5).box(2.5,1.5,2))