import cadquery as cq
w0=cq.Workplane('YZ',origin=(-63,0,0))
w1=cq.Workplane('YZ',origin=(1,0,0))
r=w0.sketch().circle(100).circle(90,mode='s').finalize().extrude(127).union(w1.sketch().arc((-55,-71),(-47,-77),(-40,-84)).segment((-40,-85)).segment((-39,-85)).arc((0,-95),(39,-85)).segment((40,-85)).segment((40,-84)).arc((95,0),(40,84)).segment((40,85)).segment((39,85)).arc((0,95),(-39,85)).segment((-40,85)).segment((-40,84)).arc((-95,7),(-55,-71)).assemble().finalize().extrude(-61))