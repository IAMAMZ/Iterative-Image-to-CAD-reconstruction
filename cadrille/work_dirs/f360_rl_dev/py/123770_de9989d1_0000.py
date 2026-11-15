import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,98))
r=w0.sketch().rect(200,197.5).push([(0,0)]).rect(51.5,52.5,mode='s').finalize().extrude(-197)