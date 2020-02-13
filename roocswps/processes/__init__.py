from .wps_say_hello import SayHello
from .wps_subset import Subset
from .wps_average import Average

processes = [
    SayHello(),
    Subset(),
    Average(),
]
