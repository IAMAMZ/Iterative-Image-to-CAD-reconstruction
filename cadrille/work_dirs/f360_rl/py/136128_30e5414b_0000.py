import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,59))
w1=cq.Workplane('XY',origin=(0,0,43))
r=w0.sketch().arc((-46,52),(-92,-30),(0,-21)).arc((29,6),(61,17.5)).segment((100,17.5)).segment((100,53)).segment((-19.5,53)).close().assemble().finalize().extrude(-117.5).union(w1.workplane(offset=-87/2).moveTo(-24.5,46.5).box(11.5,13.5,87))