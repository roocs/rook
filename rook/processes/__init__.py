from .wps_usage import Usage
from .wps_dashboard import DashboardProcess
from .wps_average import Average
from .wps_orchestrate import Orchestrate
from .wps_subset import Subset

processes = [
    Usage(),
    DashboardProcess(),
    Subset(),
    Average(),
    Orchestrate(),
]
