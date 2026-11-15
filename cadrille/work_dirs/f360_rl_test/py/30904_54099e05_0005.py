import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
w1=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().segment((-14,-60),(-12,-60)).arc((0,-68),(12,-60)).segment((14,-60)).segment((14,60)).segment((12,60)).arc((0,68),(-12,60)).segment((-14,60)).close().assemble().finalize().extrude(-198).union(w0.sketch().arc((-38,-39),(0,-79),(38,-39)).segment((38,49)).arc((0,79),(-38,49)).close().assemble().finalize().extrude(-28)).union(w1.sketch().segment((-24,-69),(24,-69)).segment((24,69)).arc((0,79),(-24,60)).close().assemble().finalize().extrude(11))