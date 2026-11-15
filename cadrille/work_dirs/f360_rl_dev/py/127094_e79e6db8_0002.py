import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-1))
r=w0.sketch().segment((-7,-100),(7,-100)).segment((7,-89)).arc((16,-76),(7,-64)).segment((5.5,100)).segment((-4.5,100)).segment((-5.5,-62)).segment((-7,-64)).arc((-16,-76),(-7,-88)).close().assemble().push([(0,-76)]).circle(8.5,mode='s').finalize().extrude(4)