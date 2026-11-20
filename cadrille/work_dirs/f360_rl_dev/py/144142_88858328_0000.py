import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-3.5,21),(0,0)).segment((0,-17)).segment((3.5,-21)).segment((4.5,-8)).arc((3,8),(-2.5,21.5)).close().assemble().finalize().extrude(-200)