import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,75))
r=w0.sketch().segment((-100,-25),(100,-25)).segment((100,25)).segment((73.5,25)).segment((73,0)).segment((-73,0)).segment((-73,25)).segment((-100,25)).close().assemble().finalize().extrude(-150)