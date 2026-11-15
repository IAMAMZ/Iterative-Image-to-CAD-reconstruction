import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().arc((37,15),(-73,0),(38,-11)).segment((57,-12)).segment((74,-2)).segment((72,5)).segment((63,12)).segment((42,16)).close().assemble().push([(-18,0)]).circle(29.5,mode='s').finalize().extrude(-200)