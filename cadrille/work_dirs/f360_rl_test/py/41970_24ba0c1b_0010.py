import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,19,0))
r=w0.sketch().arc((-10,-87),(0,-100),(8,-87)).segment((3,-78)).segment((6,-30)).segment((8,-30)).segment((8,97)).segment((7,100)).segment((-10,100)).close().assemble().push([(0,33)]).rect(8.5,123.5,mode='s').push([(0,-89)]).circle(5,mode='s').finalize().extrude(-38.5)