import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-72,0))
w1=cq.Workplane('XY',origin=(0,0,64))
r=w0.sketch().segment((-73,-64),(-57,-64)).segment((-57,-29)).segment((57,-29)).segment((57,29)).segment((-57,29)).segment((-57,64)).segment((-71,64)).close().assemble().finalize().extrude(143).union(w1.sketch().push([(0,1)]).circle(99).circle(83,mode='s').finalize().extrude(8))