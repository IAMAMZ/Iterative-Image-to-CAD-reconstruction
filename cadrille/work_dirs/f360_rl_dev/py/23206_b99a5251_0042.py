import cadquery as cq
w0=cq.Workplane('YZ',origin=(22,0,0))
r=w0.sketch().arc((-31,55),(-80,-4),(-26,-56)).arc((-9,-77),(8,-100)).segment((12,-100)).segment((12,-56)).segment((80,-55.5)).segment((80,55.5)).segment((12.5,56)).segment((12,100)).segment((5.5,100)).segment((-22,58)).close().assemble().push([(-24,0)]).circle(23,mode='s').finalize().extrude(-44)