import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().segment((-37,-83),(0,-100)).segment((37,-76)).arc((13,-1),(37,76.5)).segment((0,100)).segment((-19.5,84.5)).segment((-37,83.5)).close().assemble().push([(-13,24)]).circle(7,mode='s').push([(-12,-25)]).circle(7.5,mode='s').push([(6,-73)]).circle(7,mode='s').push([(8,73)]).circle(7.5,mode='s').finalize().extrude(-9)