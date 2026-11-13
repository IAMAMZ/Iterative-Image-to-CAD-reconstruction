import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().rect(200,194.5).push([(-77.5,0)]).rect(29.5,120.5,mode='s').push([(-49,71.5)]).rect(8.5,17.5,mode='s').push([(-49,-67.5)]).rect(13.5,29.5,mode='s').push([(-27,49.5)]).rect(6.5,71.5,mode='s').push([(0,0)]).rect(3.5,29.5).push([(0,0.5)]).circle(14.5).push([(44,-9)]).circle(45.5,mode='s').finalize().extrude(2.5)