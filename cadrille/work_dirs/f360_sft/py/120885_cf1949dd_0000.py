import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-40))
r=w0.sketch().segment((-100,-38),(85,-38)).segment((85,-22)).arc((89,28),(39,30)).arc((-5,9),(-48,-1)).arc((-76,-12),(-100,-25)).close().assemble().finalize().extrude(80)