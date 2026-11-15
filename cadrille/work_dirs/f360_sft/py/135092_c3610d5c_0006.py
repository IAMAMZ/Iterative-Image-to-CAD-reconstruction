import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,42))
r=w0.sketch().arc((39,15),(-100,-4),(40,-13)).segment((48,-15)).arc((68,-21),(88,-12)).segment((98,-12)).segment((100,7)).segment((96,7)).arc((80,20),(59,18)).segment((40,21)).close().assemble().push([(-30,0)]).circle(50,mode='s').finalize().extrude(-85)