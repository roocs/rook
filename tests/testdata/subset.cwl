#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow
inputs:
  data_ref: String

outputs:
  output:
    type: File
    outputSource: subset/output

steps:
  subset:
    run: daops.subset
    in:
      data_ref: data_ref
    out: [output]
