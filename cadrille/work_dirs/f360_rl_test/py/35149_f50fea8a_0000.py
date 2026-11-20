import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,18,0))
r=w0.sketch().rect(200,109).push([(46,0)]).circle(9.5,mode='s').finalize().extrude(-36.5)