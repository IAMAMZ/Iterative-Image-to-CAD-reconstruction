import cadquery as cq
w0=cq.Workplane('YZ',origin=(34,0,0))
r=w0.sketch().segment((-41,-12),(-30,-13)).segment((-34,-29)).segment((-25,-39)).segment((-29,-43)).segment((16,-95)).arc((35,-97),(41,-79)).segment((0,-15)).segment((-1,-12)).segment((0,79)).arc((-21,100),(-41,80)).close().assemble().push([(-22,-19)]).rect(10,11.5,mode='s').push([(29,-82.5)]).rect(4.5,3).finalize().extrude(-66.5)