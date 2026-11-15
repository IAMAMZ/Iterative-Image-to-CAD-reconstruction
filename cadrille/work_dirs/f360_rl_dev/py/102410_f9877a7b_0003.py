import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,3,0))
r=w0.sketch().push([(0,-93)]).circle(7).circle(3.5,mode='s').push([(0,0)]).rect(9.5,188.5).push([(0,93)]).circle(7).circle(3.5,mode='s').finalize().extrude(-6)