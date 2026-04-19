from dataclasses import dataclass, asdict


@dataclass
class TicketEvent:
    match_title: str
    date: str
    venue: str
    ticket_url: str
    status: str

    @property
    def key(self) -> str:
        return f"{self.match_title}|{self.date}"

    def to_dict(self) -> dict:
        return asdict(self)
