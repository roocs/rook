from .wps_average import Average
from .wps_orchestrate import Orchestrate
from .wps_subset import Subset

processes = [
    Subset(),
    Average(),
    Orchestrate(),
]
