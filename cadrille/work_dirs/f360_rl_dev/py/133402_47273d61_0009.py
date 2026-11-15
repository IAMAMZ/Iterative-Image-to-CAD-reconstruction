import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().rect(7,1).push([(0,0)]).rect(5.5,1).push([(0,-0)]).rect(5.5,1).push([(0,0)]).rect(5.5,1).finalize().extrude(-200)