import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.workplane(offset=6/2).box(120,200,6).union(w0.sketch().rect(127.5,200).rect(112,182,mode='s').finalize().extrude(13))