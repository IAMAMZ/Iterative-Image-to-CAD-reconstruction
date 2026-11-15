import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,50,0))
r=w0.sketch().segment((-88.5,-100),(19,-100)).arc((69,-75),(88,-25)).segment((88,100)).segment((58,100)).segment((58,-51)).segment((-52,-54)).segment((-58,-34)).segment((-58,100)).segment((-88.5,100)).close().assemble().finalize().extrude(-100)