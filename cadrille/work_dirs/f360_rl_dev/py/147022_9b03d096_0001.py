import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,15))
r=w0.sketch().arc((-100,-4),(-13,-85),(71,-10)).arc((100,-1),(71,10)).arc((-20,85),(-100,0)).close().assemble().push([(-15,0)]).circle(17.5,mode='s').finalize().extrude(-30)