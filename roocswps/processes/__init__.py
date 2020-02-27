from .wps_subset import Subset
from .wps_average import Average
from .wps_orchestrate import Orchestrate

processes = [
    Subset(),
    Average(),
    Orchestrate(),
]
