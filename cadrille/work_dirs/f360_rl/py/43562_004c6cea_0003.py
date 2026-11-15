import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,8,0))
w1=cq.Workplane('ZX',origin=(0,3,0))
r=w0.sketch().push([(-55,82)]).circle(11.5).push([(0,-71)]).circle(29).push([(55,82)]).circle(16.5).finalize().extrude(-12).union(w1.sketch().segment((-67,67),(-23,-54)).segment((30,-67)).segment((67,79.5)).segment((50.5,100)).segment((-30.5,100)).segment((-67,100)).close().assemble().push([(-22,57)]).rect(23.5,51.5,mode='s').push([(0,-0.5)]).rect(8.5,29.5).finalize().extrude(-3.5)).union(w1.workplane(offset=-1/2).box(1.5,1.5,1))