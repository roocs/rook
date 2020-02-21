from .wps_subset import Subset
from .wps_average import Average
# from .wps_retrieve import Retrieve
from .wps_orchestrate import Orchestrate

processes = [
    Subset(),
    Average(),
    # Retrieve(),
    Orchestrate(),
]
