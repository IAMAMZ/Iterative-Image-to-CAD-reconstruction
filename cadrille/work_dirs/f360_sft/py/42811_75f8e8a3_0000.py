import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-51,0))
w1=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-16,-5),(-1,-18)).segment((16,-8)).segment((16,8)).segment((0,18)).segment((-16,8)).close().assemble().finalize().extrude(151).union(w1.sketch().push([(0,-73)]).circle(27).reset().face(w1.sketch().segment((-10,-82),(-9,-82)).arc((0,-86),(9,-82)).segment((10,-82)).segment((10,-65)).segment((9,-65)).arc((0,-61),(-9,-65)).segment((-10,-65)).close().assemble(),mode='s').finalize().extrude(30))