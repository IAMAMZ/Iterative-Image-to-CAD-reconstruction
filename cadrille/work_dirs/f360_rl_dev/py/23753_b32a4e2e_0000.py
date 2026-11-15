import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().circle(91).circle(61,mode='s').finalize().extrude(-200)