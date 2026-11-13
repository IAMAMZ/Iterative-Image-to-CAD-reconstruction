import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,41))
r=w0.sketch().segment((-100,-38),(85,-38)).segment((85,-22)).arc((87,31),(32,28)).arc((-10,8),(-47,0)).segment((-93,-19.5)).segment((-100,-25.5)).close().assemble().finalize().extrude(-80)