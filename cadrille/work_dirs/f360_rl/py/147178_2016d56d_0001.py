import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,38,0))
r=w0.sketch().push([(0,-88.5)]).rect(6.5,24).push([(0,-45)]).rect(6.5,21).push([(0,45)]).rect(6.5,21).push([(0,0)]).rect(6.5,25).push([(0,88.5)]).rect(6.5,23.5).finalize().extrude(-75)