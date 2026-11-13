import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-51))
r=w0.sketch().arc((-100,-25),(-88,-54),(-62,-72)).segment((-62,-73)).segment((83,-73)).segment((83,-72)).arc((100,-55),(83,-37)).segment((83,-33)).segment((-35,-33)).segment((-35,19)).segment((57,19)).arc((58,21),(59,23)).arc((76,48),(60,72)).segment((-48,73)).arc((-77,64),(-100,45)).close().assemble().finalize().extrude(102)