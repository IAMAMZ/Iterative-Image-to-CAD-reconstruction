import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-1))
r=w0.sketch().segment((-85.5,-100),(86,-100)).segment((85.5,100)).segment((-3,100)).segment((-3,-12.5)).segment((-85.5,-12.5)).close().assemble().finalize().extrude(3)