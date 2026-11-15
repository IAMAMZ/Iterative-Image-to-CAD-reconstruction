import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().segment((-100,-69),(-89,-81)).segment((-59,-82)).segment((89,-81.5)).segment((100,-69)).segment((100,69)).segment((89,81)).segment((59,82)).segment((-89,81.5)).segment((-100,69)).close().assemble().rect(114.5,21.5,mode='s').finalize().extrude(-18).union(w0.workplane(offset=-6/2).box(186.5,160,6))