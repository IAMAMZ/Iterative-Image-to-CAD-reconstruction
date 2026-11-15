import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,0))
r=w0.sketch().rect(163,200).finalize().extrude(-73).union(w0.sketch().circle(59).circle(39.5,mode='s').finalize().extrude(73))