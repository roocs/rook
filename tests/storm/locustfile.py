from locust import HttpUser, between, tag, task

from tests.storm.common import (
    C3S_CMIP6_DAY_COLLECTION,
    C3S_CMIP6_MON_COLLECTION,
    WF_C3S_CMIP6_SUBSET_AVERAGE,
    execute_async,
)


class RookUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(2, 10)

    @tag("meta")
    @task
    def health(self):
        query = "/health"

        with self.client.get(query, catch_response=True, name="health") as response:
            if "<ows:Title>rook</ows:Title>" not in response.text:
                response.failure("Health response not as expected")

    @tag("meta")
    @task
    def capabilities(self):
        query = "/wps?service=WPS&request=GetCapabilities"

        with self.client.get(
            query, catch_response=True, name="capabilities"
        ) as response:
            if "<ows:Title>rook</ows:Title>" not in response.text:
                response.failure("Capabilities does not match expected XML")

    @tag("meta")
    @task
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

    @tag("subset")
    @task
    def execute_async_subset(self):
        execute_async(
            client=self.client,
            name="execute_async_subset",
            identifier="subset",
            inputs=[
                (
                    "collection",
                    C3S_CMIP6_DAY_COLLECTION,
                ),
                ("time", "1900-01-01/1900-12-30"),
            ],
        )

    @tag("subset", "collection_only")
    @task
    def execute_async_subset_collection_only(self):
        execute_async(
            client=self.client,
            name="execute_async_subset_col_only",
            identifier="subset",
            inputs=[
                (
                    "collection",
                    C3S_CMIP6_DAY_COLLECTION,
                ),
            ],
        )

    @tag("subset", "original_files")
    @task
    def execute_async_subset_original_files(self):
        execute_async(
            client=self.client,
            name="execute_async_subset_orig_files",
            identifier="subset",
            inputs=[
                (
                    "collection",
                    C3S_CMIP6_DAY_COLLECTION,
                ),
                ("time", "1900-01-01/1900-12-30"),
                ("original_files", "1"),
            ],
        )

    @tag("average")
    @task
    def execute_async_average(self):
        execute_async(
            client=self.client,
            name="execute_async_average",
            identifier="average",
            inputs=[
                (
                    "collection",
                    C3S_CMIP6_MON_COLLECTION,
                ),
                ("dims", "time"),
            ],
        )

    @tag("workflow")
    @task
    def execute_async_orchestrate(self):
        execute_async(
            client=self.client,
            name="execute_async_orchestrate",
            identifier="orchestrate",
            complex_inputs=[
                (
                    "workflow",
                    WF_C3S_CMIP6_SUBSET_AVERAGE,
                ),
            ],
        )
