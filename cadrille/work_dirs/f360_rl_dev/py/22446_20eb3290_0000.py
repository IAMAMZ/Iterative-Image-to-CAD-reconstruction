import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().rect(12,12).rect(9.5,9.5,mode='s').finalize().extrude(-200)