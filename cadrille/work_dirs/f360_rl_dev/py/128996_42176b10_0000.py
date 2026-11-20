import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,74,0))
w1=cq.Workplane('YZ',origin=(45,0,0))
r=w0.sketch().arc((-50,-49),(0,-100),(50,-49)).segment((50,100)).segment((-50,100)).close().assemble().push([(0,-50)]).circle(23.5,mode='s').finalize().extrude(-23).union(w1.sketch().push([(0,0)]).rect(148,100).circle(23.5,mode='s').finalize().extrude(55))