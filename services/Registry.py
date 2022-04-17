import json


class RegistryHandler:
    _realms: dict
    _dirty: bool
    _instance = None
    _simulate: bool

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RegistryHandler, cls).__new__(cls)
            cls._realms = {}
            cls._dirty = False
            cls._tryLoad(cls._instance)
            cls._simulate = False

        return cls._instance

    def setSimulationMode(self, simulate: bool):
        self._simulate = simulate

    def setProperty(self, realm: str, propertyKey: str, propertyValue):
        if realm not in self._realms.keys():
            self._realms[realm] = {}

        self._realms[realm][propertyKey] = propertyValue
        self._dirty = True

    def getProperty(self, realm: str, propertyKey: str, defaultValue=None):
        if realm not in self._realms.keys():
            return defaultValue

        return self._realms[realm][propertyKey]

    def _tryLoad(self):
        data = None

        try:
            with open('registry.json', 'r') as f:
                data = json.load(f)

        except FileNotFoundError:
            return

        if data is not None:
            self._realms = data

    def saveAll(self):
        if self._simulate:
            print('Save:\n{registry}'.format(registry=self._realms))
            return

        if not self._dirty:
            return

        self._dirty = False

        with open('registry.json', 'w') as f:
            json.dump(self._realms, f)
