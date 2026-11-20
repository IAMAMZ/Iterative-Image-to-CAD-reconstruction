import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().arc((-13,-71),(0,-100),(12,-71)).segment((11,66)).segment((16,74)).segment((16,89)).arc((-2,100),(-16,85)).segment((-12,67)).segment((-11,-62.5)).close().assemble().push([(0,-82)]).circle(9,mode='s').push([(0,83)]).circle(9,mode='s').finalize().extrude(3.5)