import json
from locust import HttpUser, between, task

from tests.storm.common import execute_async

CMIP6_MON_COLLECTION = (
    "CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
)

CMIP6_DAY_COLLECTION = (
    "CMIP6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.day.tas.gn.v20190710"
)

WF_SUBSET_AVERAGE = json.dumps(
    {
        "doc": "subset+average on cmip6",
        "inputs": {"ds": [CMIP6_DAY_COLLECTION]},
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


class RookUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(1, 10)

    @task(1)
    def health(self):
        query = "/health"

        with self.client.get(query, catch_response=True, name="health") as response:
            if "<ows:Title>rook</ows:Title>" not in response.text:
                response.failure("Health response not as expected")

    @task(1)
    def capabilities(self):
        query = "/wps?service=WPS&request=GetCapabilities"

        with self.client.get(
            query, catch_response=True, name="capabilities"
        ) as response:
            if "<ows:Title>rook</ows:Title>" not in response.text:
                response.failure("Capabilities does not match expected XML")

    @task(1)
    def describe_process_subset(self):
        query = (
            "/wps?service=WPS&version=1.0.0&request=DescribeProcess&identifier=subset"
        )
        with self.client.get(
            query, catch_response=True, name="describe_process"
        ) as response:
            if "<ows:Identifier>subset</ows:Identifier>" not in response.text:
                response.failure(
                    "Process description for subset does not match expected XML"
                )

    @task(1)
    def execute_async_subset(self):
        execute_async(
            client=self.client,
            name="execute_async_subset",
            identifier="subset",
            inputs=[
                (
                    "collection",
                    CMIP6_MON_COLLECTION,
                ),
                ("time", "1900-01-01/1900-12-30"),
            ],
        )

    @task(1)
    def execute_async_average(self):
        execute_async(
            client=self.client,
            name="execute_async_average",
            identifier="average",
            inputs=[
                (
                    "collection",
                    CMIP6_MON_COLLECTION,
                ),
                ("dims", "time"),
            ],
        )

    @task(1)
    def execute_async_orchestrate(self):
        execute_async(
            client=self.client,
            name="execute_async_orchestrate",
            identifier="orchestrate",
            complex_inputs=[
                (
                    "workflow",
                    WF_SUBSET_AVERAGE,
                ),
            ],
        )
