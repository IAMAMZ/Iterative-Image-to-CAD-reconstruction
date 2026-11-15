import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,0))
r=w0.sketch().rect(200,133.5).push([(-50,0)]).circle(20,mode='s').finalize().extrude(-40).union(w0.workplane(offset=40/2).moveTo(67.5,0).box(65,67,40)).union(w0.workplane(offset=40/2).moveTo(67,0.5).box(62.5,67.5,40))