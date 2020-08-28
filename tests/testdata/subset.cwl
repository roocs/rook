#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow
inputs:
  dset: String

outputs:
  output:
    type: File
    outputSource: subset/output

steps:
  subset:
    run: daops.subset
    in:
      dset: dset
    out: [output]
