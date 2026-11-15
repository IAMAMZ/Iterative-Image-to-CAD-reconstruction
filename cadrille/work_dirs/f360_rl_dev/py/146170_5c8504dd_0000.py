import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,12,0))
r=w0.sketch().segment((-44,-100),(44.5,-100)).segment((44,-33)).segment((10,0)).segment((45,33)).segment((-23,100)).segment((-44,79)).close().assemble().finalize().extrude(-22)