import cadquery as cq
w0=cq.Workplane('YZ',origin=(13,0,0))
r=w0.sketch().rect(124,200).push([(-42,-81)]).circle(14,mode='s').push([(-29,-30)]).circle(6,mode='s').push([(-30,30)]).circle(4,mode='s').push([(0,0)]).circle(10,mode='s').push([(35,82)]).circle(14,mode='s').push([(30,29)]).circle(7,mode='s').push([(30,-30)]).circle(4,mode='s').finalize().extrude(-26)