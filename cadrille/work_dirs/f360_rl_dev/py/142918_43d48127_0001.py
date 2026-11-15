import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,36))
r=w0.sketch().arc((-100,-4),(-20,-81),(62,-11)).segment((83,-13)).segment((100,-6)).segment((100,7)).segment((83,12.5)).segment((62,13)).segment((60,21)).arc((-20,81),(-100,2)).close().assemble().push([(-20,0)]).circle(35.5,mode='s').finalize().extrude(-71.5)