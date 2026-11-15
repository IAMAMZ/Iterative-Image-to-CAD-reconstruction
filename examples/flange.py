# Example CadQuery program: must assign the final solid to `result`.
import cadquery as cq

result = (
    cq.Workplane("XY").circle(30).extrude(6)                    # flange disc
    .faces(">Z").workplane().circle(14).extrude(20)             # hub
    .faces(">Z").workplane().hole(16)                           # through bore
    .faces("<Z").workplane().polarArray(22, 0, 360, 6).hole(5)  # bolt circle
    .edges(">Z").fillet(1.5)
)
