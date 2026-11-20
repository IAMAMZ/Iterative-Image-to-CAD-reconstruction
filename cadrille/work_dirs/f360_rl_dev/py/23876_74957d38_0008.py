import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,3,0))
r=w0.sketch().circle(100).circle(87,mode='s').push([(85,-20)]).rect(7.5,6).push([(85,26)]).rect(20.5,17).circle(5,mode='s').finalize().extrude(-6)