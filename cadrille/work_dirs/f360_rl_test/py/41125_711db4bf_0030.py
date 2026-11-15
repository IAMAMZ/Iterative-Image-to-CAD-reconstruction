import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().arc((-44,-19),(-34,-44),(-5,-54)).segment((25,-54)).arc((40,-37),(44,-16)).segment((44,27)).arc((32,46),(8,54)).segment((-25,53.5)).arc((-42,33),(-44,8)).close().assemble().rect(45,60.5,mode='s').finalize().extrude(-200).union(w0.workplane(offset=-109/2).box(7.5,9.5,8))