import json

C3S_CMIP6_DAY_COLLECTION = (
    "c3s-cmip6.CMIP.SNU.SAM0-UNICON.historical.r1i1p1f1.day.pr.gn.v20190323"
)
C3S_CMIP6_MON_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
)

WF_C3S_CMIP6_SUBSET_AVERAGE = json.dumps(
    {
        "doc": "subset+average on cmip6",
        "inputs": {"ds": [C3S_CMIP6_DAY_COLLECTION]},
        "outputs": {"output": "average_ds/output"},
        "steps": {
            "subset_ds": {
                "run": "subset",
                "in": {"collection": "inputs/ds", "time": "1860-01-01/1900-12-31"},
            },
            "average_ds": {
                "run": "average",
                "in": {"collection": "subset_ds/output", "dims": "time"},
            },
        },
    }
)
