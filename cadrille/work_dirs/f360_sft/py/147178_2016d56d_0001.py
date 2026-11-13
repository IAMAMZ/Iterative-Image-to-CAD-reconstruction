import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,37,0))
r=w0.sketch().push([(0,-88)]).rect(6,24).push([(0,-1)]).rect(6,24).push([(0,88)]).rect(6,24).finalize().extrude(-75)