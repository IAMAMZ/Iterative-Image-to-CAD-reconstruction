import cadquery as cq
w0=cq.Workplane('YZ',origin=(17,0,0))
r=w0.workplane(offset=-34/2).moveTo(0,0).box(35.5,61,34).union(w0.sketch().segment((-36,-33),(35,-33)).arc((100,0),(35,29)).segment((-30,27)).arc((-99,9),(-36,-33)).assemble().push([(-60,0)]).circle(13.5,mode='s').push([(60,0)]).circle(13.5,mode='s').finalize().extrude(-15))