import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-72))
w1=cq.Workplane('YZ',origin=(72,0,0))
r=w0.sketch().segment((-50,-57),(100,-56)).segment((100,57)).segment((-50,57)).arc((-100,0),(-50,-57)).assemble().push([(-45,0)]).circle(35,mode='s').finalize().extrude(-28).union(w1.sketch().segment((-57,-69),(57,-69)).segment((57,59)).arc((10,99),(-55,79)).segment((-57,57.5)).close().assemble().push([(0,44)]).circle(35.5,mode='s').finalize().extrude(28)).union(w1.workplane(offset=8/2).moveTo(49,-9.5).box(6,1.5,6))