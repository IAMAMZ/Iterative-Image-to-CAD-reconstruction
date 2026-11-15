import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().rect(23,21).rect(20,18,mode='s').finalize().extrude(-200)