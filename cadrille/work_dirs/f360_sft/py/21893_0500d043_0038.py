import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-41))
r=w0.sketch().rect(80,200).rect(56,96,mode='s').finalize().extrude(81)