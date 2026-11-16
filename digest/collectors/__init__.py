from digest.collectors.base import Collector
from digest.collectors.cncf import CncfCollector
from digest.collectors.devevent import DevEventCollector
from digest.collectors.onoffmix import OnoffmixCollector

ALL_COLLECTORS: list[Collector] = [DevEventCollector(), OnoffmixCollector(), CncfCollector()]
