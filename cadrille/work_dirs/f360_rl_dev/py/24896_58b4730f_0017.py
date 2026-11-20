import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,31))
r=w0.sketch().arc((-100,-4),(-17,-84),(70,-9)).segment((89,-10)).segment((100,-4)).segment((99,7)).segment((80,11)).segment((69,14)).arc((-20,84),(-100,0)).close().assemble().finalize().extrude(-60)