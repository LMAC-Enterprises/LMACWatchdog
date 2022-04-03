import glob


class TemplateEngine:
    TEMPLATES_META_PATH = 'templates'

    templates: dict
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TemplateEngine, cls).__new__(cls)
            cls._templates = {}
            cls._tryLoad(cls._instance)

        return cls._instance

    def _tryLoad(self):
        filenames = glob.glob(TemplateEngine.TEMPLATES_META_PATH + "/*/*.md", )
        filenameStripSize = len(self.TEMPLATES_META_PATH) + 1
        for filePath in filenames:
            filename = filePath[filenameStripSize:]
            fileContent = self._loadTemplateFile(filePath)
            if not fileContent:
                continue
            self._templates[filename] = fileContent

    @staticmethod
    def _loadTemplateFile(filePath: str) -> str:
        contents = ''
        try:
            with open(filePath) as f:
                contents = f.readlines()
        except OSError:
            return None

        return contents

    def createContent(self, templateFilename: str, **kwargs) -> str:
        if templateFilename not in self._templates:
            return ''

        return self._templates[templateFilename].format(**kwargs)



