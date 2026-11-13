import cadquery as cq
w0=cq.Workplane('YZ',origin=(34,0,0))
w1=cq.Workplane('XY',origin=(0,0,0))
r=w0.workplane(offset=66/2).moveTo(0,-19.5).box(68,41,66).union(w1.sketch().rect(200,134).push([(-50,0)]).circle(20,mode='s').finalize().extrude(-40))