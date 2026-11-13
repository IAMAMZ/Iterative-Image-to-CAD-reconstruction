import cadquery as cq
w0=cq.Workplane('YZ',origin=(-94,0,0))
r=w0.sketch().segment((-13,-100),(13,-100)).segment((13,100)).segment((-13,100)).segment((-13,88)).segment((7,88)).segment((7,-88)).segment((-13,-88)).close().assemble().finalize().extrude(188)