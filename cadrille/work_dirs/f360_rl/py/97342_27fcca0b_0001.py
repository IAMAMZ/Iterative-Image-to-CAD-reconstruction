import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,10))
r=w0.sketch().arc((-33,-35),(0,-100),(33,-35)).segment((38,-8)).segment((41,18)).segment((41,26)).arc((0,100),(-41,27)).segment((-42,0)).close().assemble().push([(0,-60)]).circle(31,mode='s').push([(0,10)]).circle(31,mode='s').finalize().extrude(-19.5)