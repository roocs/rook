from .wps_say_hello import SayHello
from .wps_subset import Subset
from .wps_average import Average
from .wps_retrieve import Retrieve

processes = [
    SayHello(),
    Subset(),
    Average(),
    Retrieve(),
]
