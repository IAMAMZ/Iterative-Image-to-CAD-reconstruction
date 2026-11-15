import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,19,0))
r=w0.sketch().segment((-63,-38),(63,-38)).arc((100,0),(63,38)).segment((-63,38)).arc((-100,0),(-63,-38)).assemble().finalize().extrude(-37.5)