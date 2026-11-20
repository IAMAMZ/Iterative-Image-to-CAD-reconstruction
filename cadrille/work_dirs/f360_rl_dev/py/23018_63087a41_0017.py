import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,68))
r=w0.sketch().arc((-100,-4),(-17,-84),(70,-11)).segment((87,-11)).segment((100,-4)).segment((98,7)).segment((87,11)).segment((70,12)).arc((-20,84),(-100,0)).close().assemble().finalize().extrude(-135.5)