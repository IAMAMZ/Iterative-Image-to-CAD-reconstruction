import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,5))
r=w0.sketch().arc((-8,-67),(0,-100),(8,-67)).segment((8.5,92)).arc((0,100),(-8.5,92)).close().assemble().push([(0,-83)]).circle(13,mode='s').push([(0,91)]).rect(7,9,mode='s').finalize().extrude(-8.5)