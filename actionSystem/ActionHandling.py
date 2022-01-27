from abc import ABC, abstractmethod


class PolicyAction(ABC):
    @abstractmethod
    def onActionRequest(self, actionParameters: dict):
        pass


class PolicyActionSupervisor:
    def __init__(self, actionsInfo: dict):
        self._suggestedActions = []

    def triggerAction(self, actionId: str):
        pass

    def processActions(self):
        pass

    def suggestAction(self, action: PolicyAction):
        self._suggestedActions.append(action)
