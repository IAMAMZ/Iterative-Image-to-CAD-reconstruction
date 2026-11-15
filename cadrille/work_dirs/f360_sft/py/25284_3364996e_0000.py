import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,8))
r=w0.sketch().segment((-100,-30),(45,5)).segment((74,5)).segment((100,30)).arc((77,17),(51,11)).segment((-88,-26)).arc((-94,-25),(-100,-24)).close().assemble().finalize().extrude(-16)