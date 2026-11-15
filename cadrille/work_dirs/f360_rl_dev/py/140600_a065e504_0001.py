import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-79))
w1=cq.Workplane('YZ',origin=(63,0,0))
r=w0.sketch().segment((-96,28),(-19,-26)).segment((29,-40)).segment((31,-38)).arc((96,40),(19,100)).segment((-29,81.5)).close().assemble().push([(22,30)]).circle(62.5,mode='s').finalize().extrude(2).union(w0.sketch().push([(26,-98.5)]).circle(1.5).push([(26,39)]).rect(2,2).finalize().extrude(157)).union(w1.workplane(offset=-75/2).moveTo(-97,75.5).box(6,7,75)).union(w1.workplane(offset=-74/2).moveTo(38.5,75.5).box(5.5,7,74))