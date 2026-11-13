import cadquery as cq
w0=cq.Workplane('YZ',origin=(4,0,0))
r=w0.sketch().segment((-11,-96),(-7,-100)).segment((9,-100)).segment((11,-96)).segment((11,96)).segment((7,100)).segment((-9,100)).segment((-11,96)).close().assemble().push([(-0.5,-90)]).rect(5.5,6).finalize().extrude(-8)