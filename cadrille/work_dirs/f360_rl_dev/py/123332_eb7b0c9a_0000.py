import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,25))
r=w0.sketch().segment((-100,0),(-61,-40)).segment((100,-40)).segment((100,-25)).segment((56,-25)).segment((54,17)).arc((36,40),(15,20)).segment((16,-25)).segment((-49,-25)).segment((-89,10)).close().assemble().finalize().extrude(-50)