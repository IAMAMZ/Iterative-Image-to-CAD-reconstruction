import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-21,0),(-15,0)).arc((0,-3),(18,-2)).segment((21,0)).segment((18,1)).arc((0,-2),(-17,3)).close().assemble().finalize().extrude(-200)