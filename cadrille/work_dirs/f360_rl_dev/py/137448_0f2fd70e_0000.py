import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,2))
r=w0.sketch().segment((-95,-9),(-9,-9)).segment((-9,-94)).arc((0,-100),(9.5,-94)).segment((9,-9)).segment((95,-9)).arc((99,4),(95,9)).segment((9.5,9.5)).segment((9,94.5)).segment((7.5,100)).segment((-9,99)).segment((-9,9)).segment((-95,9)).arc((-100,0),(-95,-8)).close().assemble().finalize().extrude(-3)