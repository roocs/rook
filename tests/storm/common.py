import os
import time
from jinja2 import FileSystemLoader, Environment
import locust
from pyquery import PyQuery
from urllib.parse import urlparse
import gevent


templates_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates")
template_env = Environment(loader=FileSystemLoader(templates_path), autoescape=True)


def execute_async(client, name, identifier, inputs=None, complex_inputs=None):
    """
    The async request is taken from:
    https://github.com/pglass/how-do-i-locust
    """
    inputs = inputs or []
    complex_inputs = complex_inputs or []
    data = build_execute_request(identifier, inputs, complex_inputs)
    gevent.spawn(do_execute_async, client=client, name=name, data=data)


def build_execute_request(identifier, inputs, complex_inputs):
    execute_template = template_env.get_template("execute.xml")
    return execute_template.render(
        identifier=identifier, inputs=inputs, complex_inputs=complex_inputs
    )


def async_success(name, start_time, resp):
    locust.events.request_success.fire(
        request_type=resp.request.method,
        name=name,
        response_time=int((time.monotonic() - start_time) * 1000),
        response_length=len(resp.content),
    )


def async_failure(name, start_time, resp, message):
    locust.events.request_failure.fire(
        request_type=resp.request.method,
        name=name,
        response_time=int((time.monotonic() - start_time) * 1000),
        response_length=len(resp.content),
        exception=Exception(message),
    )


def get_status_location(xml):
    pq = PyQuery(xml)
    status_location = pq.attr("statusLocation")
    return urlparse(status_location).path


def parse_exception(xml):
    pq = PyQuery(xml)
    return pq.text()


def do_execute_async(client, name, data, timeout=600):
    start_time = time.monotonic()
    # name = "execute_async_subset"
    resp = client.post("/wps", data=data, name=name)
    if not resp.ok:
        if "Exception" in resp.text:
            error_message = parse_exception(resp.content)
            async_failure(name, start_time, resp, f"Failed: {error_message}")
        else:
            async_failure(name, start_time, resp, "Failed: HTTP error")
        return
    elif "ProcessAccepted" not in resp.text:
        async_failure(name, start_time, resp, "Process not accepted")
        return
    # get status location
    status_location = get_status_location(resp.content)

    # Now poll for an ACTIVE status
    end_time = start_time + timeout
    name_poll = f"{name}_poll"
    while time.monotonic() < end_time:
        resp_poll = client.get(status_location, name=name_poll)
        if not resp_poll.ok:
            async_failure(
                name_poll,
                start_time,
                resp,
                f"Failed - HTTP error: {status_location}",
            )
            return
        elif "ProcessSucceeded" in resp_poll.text:
            async_success(name_poll, start_time, resp_poll)
            return
        elif "ProcessFailed" in resp_poll.text:
            error_message = parse_exception(resp_poll.content)
            async_failure(
                name_poll,
                start_time,
                resp_poll,
                f"Failed - {error_message}: {status_location}",
            )
            return

        # IMPORTANT: Sleep must be monkey-patched by gevent (typical), or else
        # use gevent.sleep to avoid blocking the world.
        gevent.sleep(2)
    async_failure(
        name_poll,
        start_time,
        resp_poll,
        f"Failed - timed out after {timeout} seconds: {status_location}",
    )
