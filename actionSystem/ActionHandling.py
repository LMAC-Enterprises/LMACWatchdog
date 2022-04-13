from abc import ABC, abstractmethod

class PolicyAction(ABC):
    @abstractmethod
    def onActionRequest(self):
        pass


class PolicyActionSupervisor:
    _suggestedActions: list

    def __init__(self):
        self._suggestedActions = []

    def processActions(self):
        for suggestedAction in self._suggestedActions:
            suggestedAction.onActionRequest()

    def suggestAction(self, action: PolicyAction):
        self._suggestedActions.append(action)
