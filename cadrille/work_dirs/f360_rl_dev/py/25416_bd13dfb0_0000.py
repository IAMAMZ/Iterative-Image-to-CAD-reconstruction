import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,40,0))
r=w0.sketch().rect(200,80).push([(0,-0)]).rect(157,50.5,mode='s').finalize().extrude(-80)