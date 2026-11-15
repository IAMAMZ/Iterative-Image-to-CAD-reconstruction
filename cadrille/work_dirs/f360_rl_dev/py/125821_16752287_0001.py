import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().arc((-41,-12),(0,-47),(41,-8)).arc((0,41),(-41,8)).close().assemble().finalize().extrude(-200).union(w0.sketch().circle(74).finalize().extrude(-89))