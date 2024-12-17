from dataclasses import dataclass
from typing import List, Optional

@dataclass
class BacklogQueryResult:
    backlog_items: List[dict]
    display_fields: List[str]

    start_earliest: Optional[str]
    end_latest: Optional[str]

    rfc_ratio: int
    committed_ratio: int

    total_logged: float
    total_remaining: float

    include_done: bool