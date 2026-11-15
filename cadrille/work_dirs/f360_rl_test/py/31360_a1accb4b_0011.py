import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,25,0))
r=w0.sketch().circle(100).circle(62.5,mode='s').finalize().extrude(-50)