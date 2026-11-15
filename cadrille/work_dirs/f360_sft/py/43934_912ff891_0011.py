import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,15,0))
r=w0.sketch().rect(100,200).push([(0,-69)]).circle(19,mode='s').push([(0,69)]).circle(19,mode='s').finalize().extrude(-30).union(w0.sketch().arc((-10,-99),(19,-71),(28,-32)).close().assemble().reset().face(w0.sketch().segment((10,99),(19,87)).arc((15,93),(10,99)).assemble()).finalize().extrude(-18))