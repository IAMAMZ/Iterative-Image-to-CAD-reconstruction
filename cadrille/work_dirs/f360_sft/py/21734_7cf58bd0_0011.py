import cadquery as cq
w0=cq.Workplane('YZ',origin=(9,0,0))
r=w0.sketch().rect(200,120).push([(-81,-44)]).circle(7,mode='s').push([(-81,44)]).circle(7,mode='s').push([(-26,-41)]).circle(7,mode='s').push([(-26,41)]).circle(7,mode='s').push([(26,-41)]).circle(7,mode='s').push([(27,42)]).circle(7,mode='s').push([(79,-44)]).circle(7,mode='s').push([(81,44)]).circle(7,mode='s').finalize().extrude(-18)