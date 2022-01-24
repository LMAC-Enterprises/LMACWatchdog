from abc import ABC, abstractmethod


class Action(ABC):
    @abstractmethod
    def onActionRequest(self, actionParameters: dict):
        pass


class ActionManager:
    def __init__(self, actionsInfo: dict):
        self._actions = {}

    def triggerAction(self, actionId: str):
        pass
