import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,23))
r=w0.workplane(offset=-46.5/2).moveTo(0,-93).box(170,14,46.5).union(w0.sketch().segment((-39,-100),(85,-100)).segment((83,0)).arc((-30,94),(-39,-66)).close().assemble().finalize().extrude(-33.5)).union(w0.sketch().push([(-0,-0.5)]).rect(170,196).circle(69.5,mode='s').finalize().extrude(-20.5))