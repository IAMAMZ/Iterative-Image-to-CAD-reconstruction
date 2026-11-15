import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().rect(10,10).rect(9,9,mode='s').finalize().extrude(-200)