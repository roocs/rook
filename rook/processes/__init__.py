from .wps_usage import Usage
from .wps_dashboard import DashboardProcess
from .wps_average_time import AverageByTime
from .wps_average_dim import AverageByDimension
from .wps_average_weighted import WeightedAverage
from .wps_orchestrate import Orchestrate
from .wps_subset import Subset
from .wps_concat import Concat

processes = [
    Usage(),
    DashboardProcess(),
    Subset(),
    AverageByTime(),
    AverageByDimension(),
    WeightedAverage(),
    Concat(),
    Orchestrate(),
]
