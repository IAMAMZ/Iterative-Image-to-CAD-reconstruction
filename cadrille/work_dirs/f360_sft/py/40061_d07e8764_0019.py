import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-94))
r=w0.sketch().arc((83,-6),(91,-6),(100,-2)).arc((98,2),(100,6)).arc((91,10),(83,10)).arc((-100,-2),(83,-6)).assemble().reset().face(w0.sketch().segment((-18,-28),(8,-28)).segment((8,-21)).arc((18,0),(8,21)).segment((8,28)).segment((-18,28)).segment((-18,21)).arc((-29,0),(-18,-21)).close().assemble(),mode='s').finalize().extrude(188)