import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-7,0))
r=w0.sketch().arc((-15,-88),(0,-100),(15,-88)).segment((15,88)).segment((15,89)).segment((15,90)).segment((15,91)).arc((0,100),(-15,91)).segment((-15,89)).segment((-15,88)).close().assemble().push([(0,83)]).circle(11,mode='s').push([(0,-83)]).circle(11,mode='s').finalize().extrude(14)