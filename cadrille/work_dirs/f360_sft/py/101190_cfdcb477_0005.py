import cadquery as cq
w0=cq.Workplane('YZ',origin=(-17,0,0))
r=w0.workplane(offset=30/2).moveTo(0,-14.5).box(154,63,30).union(w0.sketch().segment((-100,-46),(-60,-46)).arc((11,-1),(83,-1)).arc((90,10),(100,18)).segment((100,31)).arc((75,44),(47,45)).arc((1,20),(-47,20)).arc((-82,-7),(-100,-46)).assemble().finalize().extrude(34))