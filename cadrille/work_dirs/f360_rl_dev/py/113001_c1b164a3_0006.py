import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().push([(-29,30)]).circle(31).circle(24,mode='s').push([(29,30)]).circle(31).circle(25,mode='s').finalize().extrude(-200).union(w0.workplane(offset=-100/2).moveTo(28.5,-29).box(25,63.5,100)).union(w0.workplane(offset=-89/2).moveTo(29,30.5).box(1.5,1.5,8))