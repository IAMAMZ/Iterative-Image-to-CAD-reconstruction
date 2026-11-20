import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-42))
r=w0.workplane(offset=4.5/2).moveTo(0,0.5).box(154.5,192.5,4.5).union(w0.sketch().segment((-83.5,-88),(-76,-100)).segment((76,-100)).segment((83.5,-88)).segment((83.5,88)).segment((76,100)).segment((-76,100)).segment((-83,88)).close().assemble().push([(0,0)]).rect(150,182,mode='s').finalize().extrude(83))