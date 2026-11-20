import cadquery as cq
w0=cq.Workplane('YZ',origin=(-40,0,0))
r=w0.sketch().circle(100).circle(66.5,mode='s').circle(50).circle(7.5,mode='s').push([(27,37.5)]).rect(39.5,29.5).finalize().extrude(14.5).union(w0.sketch().circle(100).circle(70,mode='s').finalize().extrude(80))