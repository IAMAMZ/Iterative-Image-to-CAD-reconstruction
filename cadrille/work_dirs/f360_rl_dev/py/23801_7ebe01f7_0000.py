import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-43,-15),(0,-15)).segment((0,-25.5)).segment((43,-25)).segment((43,-18)).segment((22,-18)).segment((22,25)).segment((0,25)).segment((-1,4)).segment((-43,3)).close().assemble().finalize().extrude(-200)