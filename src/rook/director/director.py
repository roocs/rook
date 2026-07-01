from pywps.app.exceptions import ProcessError

from .execution import execute_request


def wrap_director(collection, inputs, runner):
    # Ask director whether request should be rejected, use original files or apply WPS process
    try:
        return execute_request(collection, inputs, runner)
    except Exception as e:
        raise ProcessError(f"{e}")
