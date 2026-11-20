import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,12,0))
r=w0.sketch().arc((-12,-55),(0,-100),(12,-55)).segment((9.5,0)).segment((12,71.5)).arc((0,100),(-9,71)).segment((-9.5,6)).close().assemble().push([(0,-75)]).circle(12,mode='s').push([(0,84)]).circle(8.5,mode='s').finalize().extrude(-24)