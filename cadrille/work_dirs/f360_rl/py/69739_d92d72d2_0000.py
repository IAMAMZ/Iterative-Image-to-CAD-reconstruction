import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().push([(0,0)]).rect(81.5,140).push([(16.5,7.5)]).rect(33,113.5,mode='s').finalize().extrude(99.5).union(w0.sketch().segment((-41,-70),(41,-70)).segment((41,-65.5)).segment((-37,-65)).segment((-37,70)).segment((-41,70)).close().assemble().finalize().extrude(200))