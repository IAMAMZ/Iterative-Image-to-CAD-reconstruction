import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,5))
r=w0.sketch().circle(100).push([(0,0)]).rect(25,44.5,mode='s').finalize().extrude(-8)