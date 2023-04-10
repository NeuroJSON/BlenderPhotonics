from abc import ABC, abstractmethod, abstractproperty
from collections import namedtuple
from pathlib import Path


PackageBrief = namedtuple('PackageBrief', ['name', 'probe_fun'])


M_SCRIPTS = Path(__file__).parent / 'script'
OUTPUT_DIR = Path(__file__).parent / 'out'
GATEWAY_DIR = Path(__file__).parent / 'gateway'
PACKAGES = [PackageBrief(name='jsonlab', probe_fun='loadjson'),
            PackageBrief(name='iso2mesh', probe_fun='s2m')]


class BackendABC(ABC):
    @abstractmethod
    def __init__(self, engine_type: str):
        pass

    @

class OctaveBackend(BackendABC):
    def __init__(self, engine_type: str):
        self.engine_type = engine_type.lower()
        if self.engine_type == 'octave':
            self.EngineError2 = self.EngineError1 = __import__('oct2py.utils', globals(), locals(), ['Oct2PyError'], 0)
            self.engine = __import__('oct2py', globals(), locals(), ['Oct2Py'], 0)
        else:
            matlab_stuff = __import__('matlab.engine', globals(), locals(), ['MatlabEngine',
                                                                             'MatlabExecutionError',
                                                                             'RejectedExecutionError'], 0)
            self.EngineError1 = matlab_stuff.MatlabExecutionError
            self.EngineError1 = matlab_stuff.RejectedExecutionError
            self.engine = matlab_stuff.MatlabEngine

    def __getattr__(self, item):
        def inner(*args, nout: int = 0):
            with self.engine() as engine:
                # import
                engine.addpath(M_SCRIPTS)
                try:
                    packages_to_load = filter(lambda p: p['name'] in PACKAGES, engine.pkg('list').tolist()[0])
                    for package in packages_to_load:
                        engine.addpath(str(Path(package['dir'])))
                except IndexError:
                    raise ImportError('No local packages installed for Octave')  # TODO: another exception type
                try:
                    return engine.feval(item, *args, nargout=nout)
                except self.EngineError1:
                    return engine.feval(item, *args, nout=nout)
        return inner


def get_backend(engine_type='octave'):
    return Backend(engine_type)
