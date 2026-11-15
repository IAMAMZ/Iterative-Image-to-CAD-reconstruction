import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,4))
r=w0.sketch().rect(78.5,200).rect(69,193.5,mode='s').finalize().extrude(-6.5)