import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().segment((-52,-100),(52,-100)).segment((52,100)).segment((-52,100)).close().assemble().push([(-46,93.5)]).rect(4,5).push([(-44,-93.5)]).rect(4,3.5).push([(46,-93.5)]).rect(4,3.5).finalize().extrude(2.5)