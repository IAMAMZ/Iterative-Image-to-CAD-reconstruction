import cadquery as cq
w0=cq.Workplane('YZ',origin=(13,0,0))
r=w0.sketch().rect(166.5,200).push([(0,0)]).rect(152,187.5,mode='s').finalize().extrude(-24)