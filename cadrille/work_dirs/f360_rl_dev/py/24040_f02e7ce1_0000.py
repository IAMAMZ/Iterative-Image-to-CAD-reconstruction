import cadquery as cq
w0=cq.Workplane('YZ',origin=(44,0,0))
w1=cq.Workplane('YZ',origin=(64,0,0))
r=w0.workplane(offset=-108/2).moveTo(-86.5,0).box(27,109,108).union(w0.sketch().segment((-100,-54),(40,-40)).segment((50,36.5)).segment((-70,51.5)).segment((-100,54)).close().assemble().finalize().extrude(-20)).union(w1.sketch().push([(61,0)]).circle(39).circle(18.5,mode='s').finalize().extrude(-46)).union(w1.workplane(offset=-2/2).moveTo(97,0.5).box(2.5,1.5,1))