import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-33,-57),(-15,-57)).segment((-15,-100)).segment((22,-100)).segment((33,-20)).segment((26,-20)).arc((-11,-11),(-11,27)).segment((-11,29)).segment((16,59)).segment((7,100)).segment((-15,95)).segment((-33,44)).close().assemble().push([(1,-90)]).circle(5,mode='s').finalize().extrude(10)