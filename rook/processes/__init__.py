from .wps_usage import Usage
from .wps_average import Average
from .wps_orchestrate import Orchestrate
from .wps_subset import Subset

processes = [
    Usage(),
    Subset(),
    Average(),
    Orchestrate(),
]
