import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,3,0))
r=w0.sketch().segment((-96,20),(-47,18)).segment((-25,2)).segment((-12,-24)).segment((-1,-45)).segment((9,-43.5)).segment((10,18.5)).segment((96,19.5)).arc((100,33),(96,44)).segment((-12.5,44.5)).segment((-96,44)).arc((-100,32),(-96,23)).close().assemble().push([(0,31.5)]).rect(6,3.5).finalize().extrude(-6)