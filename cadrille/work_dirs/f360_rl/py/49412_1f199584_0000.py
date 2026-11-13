import cadquery as cq
w0=cq.Workplane('YZ',origin=(13,0,0))
r=w0.sketch().rect(125,200).push([(-42,-82)]).circle(14,mode='s').push([(-31,31)]).circle(3,mode='s').push([(0,0)]).circle(10,mode='s').push([(42,80)]).circle(13.5,mode='s').push([(-31,-31)]).circle(5,mode='s').push([(31,-31)]).circle(2.5).push([(31,31)]).circle(6.5,mode='s').finalize().extrude(-25)