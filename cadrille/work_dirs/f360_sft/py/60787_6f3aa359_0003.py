import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,1,0))
r=w0.sketch().rect(200,162).push([(-33,0)]).rect(2,108,mode='s').push([(33,0)]).rect(2,108,mode='s').finalize().extrude(-2)