import cadquery as cq
w0=cq.Workplane('YZ',origin=(-1,0,0))
r=w0.sketch().segment((-21,99),(-7,69)).segment((-7,-86)).arc((6,-100),(21,-86)).segment((21,73)).segment((4,72)).close().assemble().push([(6.5,-46)]).rect(11.5,63.5,mode='s').push([(6.5,22)]).rect(11.5,53.5,mode='s').push([(6,-86)]).rect(10,11.5,mode='s').finalize().extrude(3.5)