import cadquery as cq
w0=cq.Workplane('YZ',origin=(-62.5,0,0))
r=w0.sketch().segment((-96,-35),(-14,-100)).segment((77,-64.5)).segment((96,38)).segment((15,100)).segment((-77,64.5)).close().assemble().finalize().extrude(7.5).union(w0.sketch().push([(-50.5,-21)]).rect(7,17).push([(-37.5,32)]).rect(7,17).push([(50,-39)]).rect(7,17).push([(60.5,14.5)]).rect(8,19).finalize().extrude(125))