import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,87,0))
w1=cq.Workplane('YZ',origin=(-96,0,0))
r=w0.sketch().segment((-100,-100),(100,-100)).segment((100,-22)).segment((94,-22)).segment((94,-92)).segment((-94,-92)).segment((-94,92)).segment((-39,92)).segment((-39,100)).segment((-100,100)).close().assemble().finalize().extrude(-175).union(w0.sketch().segment((-16,-93),(44,-93)).segment((44,-36)).segment((41,-36)).segment((41,-53)).segment((-16,-53)).close().assemble().finalize().extrude(-39)).union(w1.workplane(offset=188/2).moveTo(0,-65).box(26,68,188))