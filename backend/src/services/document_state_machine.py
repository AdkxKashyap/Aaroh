from src.enums.document_status import DocumentStatus


class DocumentStateMachine:

    _TRANSITIONS = {
        DocumentStatus.UPLOADED: {
            DocumentStatus.PARSING,
        },
        DocumentStatus.PARSING: {
            DocumentStatus.PARSED,
        },
        DocumentStatus.PARSED: {
            DocumentStatus.CLARIFICATION,
            DocumentStatus.AWAITING_APPROVAL,
        },
        DocumentStatus.CLARIFICATION: {
            DocumentStatus.PARSED,
            DocumentStatus.AWAITING_APPROVAL,
        },
        DocumentStatus.AWAITING_APPROVAL: {
            DocumentStatus.APPROVED,
        },
        DocumentStatus.APPROVED: {
            DocumentStatus.APPLIED,
        },
    }

    @classmethod
    def can_transition(
        cls,
        current: DocumentStatus,
        target: DocumentStatus,
    ) -> bool:
        return target in cls._TRANSITIONS.get(current, set())

    @classmethod
    def transition(
        cls,
        current: DocumentStatus,
        target: DocumentStatus,
    ) -> DocumentStatus:
        if not cls.can_transition(current, target):
            raise ValueError(f"Invalid document transition: " f"{current} -> {target}")

        return target
