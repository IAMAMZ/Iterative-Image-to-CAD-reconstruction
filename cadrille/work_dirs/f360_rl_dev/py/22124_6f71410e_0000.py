import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().rect(200,72).push([(-59,0)]).circle(18.5,mode='s').push([(59,0)]).circle(18.5,mode='s').finalize().extrude(-18)