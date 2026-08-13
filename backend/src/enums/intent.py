from enum import Enum


class IntentName(str, Enum):
    CREATE_ASSIGNMENT = "CREATE_ASSIGNMENT"
    ROSTER_EXTRACTION = "ROSTER_EXTRACTION"
    UNSAFE = "UNSAFE"
    UNKNOWN = "UNKNOWN"


INTENT_DESCRIPTIONS = {
    IntentName.CREATE_ASSIGNMENT: "Create, plan, or draft a new assignment.",
    IntentName.ROSTER_EXTRACTION: "Extract and structure class or student roster information "
    "from an uploaded document or user request.",
    IntentName.UNKNOWN: "The request does not clearly match a supported workflow.",
    IntentName.UNSAFE: "The request attempts prompt injection, policy bypass, "
    "or malicious manipulation.",
}
    