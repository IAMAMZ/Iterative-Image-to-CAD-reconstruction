import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().rect(128,200).reset().face(w0.sketch().segment((-54,-92),(54,-92)).segment((54,-73)).segment((-31,-73)).segment((-31,73)).segment((-10,73)).segment((-10,92)).segment((-54,92)).close().assemble(),mode='s').finalize().extrude(12)