import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-41))
w1=cq.Workplane('ZX',origin=(0,3,0))
r=w0.sketch().push([(-77,0)]).rect(46,46.5).circle(21.5,mode='s').finalize().extrude(24.5).union(w0.sketch().push([(-74,-3.5)]).circle(24.5).circle(20.5,mode='s').push([(85.5,0.5)]).rect(29.5,1.5).finalize().extrude(84)).union(w1.sketch().segment((-41,-46),(41,-46)).segment((41,71.5)).segment((40,100)).segment((-41,100)).close().assemble().push([(-0,44)]).circle(12.5,mode='s').finalize().extrude(-27)).union(w1.workplane(offset=-9.5/2).moveTo(0,97.5).box(1.5,1,1.5))