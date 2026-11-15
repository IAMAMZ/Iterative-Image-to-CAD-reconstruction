import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().rect(69,200).push([(0,-72)]).circle(17.5,mode='s').push([(0,-2)]).circle(17.5,mode='s').push([(0,66)]).circle(17.5,mode='s').push([(0,-2)]).rect(5.5,5).finalize().extrude(-13.5)