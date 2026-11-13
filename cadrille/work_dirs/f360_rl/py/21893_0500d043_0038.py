import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,41))
r=w0.sketch().rect(80.5,200).push([(2,0)]).rect(53.5,95,mode='s').finalize().extrude(-81.5).union(w0.workplane(offset=-24/2).box(79.5,200,24))