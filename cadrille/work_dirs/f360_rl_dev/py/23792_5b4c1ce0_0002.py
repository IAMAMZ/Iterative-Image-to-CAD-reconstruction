import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().rect(8.5,8.5).rect(7,7,mode='s').finalize().extrude(-200)