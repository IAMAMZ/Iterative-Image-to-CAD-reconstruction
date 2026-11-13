import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,8))
r=w0.sketch().rect(200,200).push([(0,0)]).rect(177.5,174,mode='s').finalize().extrude(-14.5)