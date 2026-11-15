import cadquery as cq
w0=cq.Workplane('YZ',origin=(14,0,0))
w1=cq.Workplane('YZ',origin=(6,0,0))
r=w0.sketch().arc((-100,-11),(-92,-26),(-71,-35)).segment((71,-43.5)).segment((92,-28)).segment((100,-11)).segment((100,31.5)).segment((92,43.5)).segment((-92.5,43.5)).segment((-100,31.5)).close().assemble().push([(0,4.5)]).rect(192.5,71.5,mode='s').finalize().extrude(-28).union(w1.workplane(offset=-1/2).moveTo(0,-38).box(1.5,8,1))