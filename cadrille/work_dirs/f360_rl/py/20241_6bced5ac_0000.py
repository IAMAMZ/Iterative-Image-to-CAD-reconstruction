import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.workplane(offset=22/2).box(200,79.5,22).union(w0.sketch().rect(200,80).push([(48,0)]).rect(17.5,35.5,mode='s').finalize().extrude(40))