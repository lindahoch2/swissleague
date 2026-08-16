from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class CompetitionResult:
    rank: int
    points: float
    counts: bool = True

    def to_dict(self):
        return {"rank": self.rank, "points": self.points, "counts": self.counts}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

@dataclass
class Athlete:
    civl_id: str
    name: str
    first_name: str
    gender: str
    nat: str
    glider: str
    birth_year: int
    total_points: float = 0.0
    competitions: Dict[str, CompetitionResult] = field(default_factory=dict)

    def update_total_points(self, new_points: float, new_comp_key: str):
        """Encapsulated business logic for calculating the top 4 results."""
        if len(self.competitions) <= 4:
            self.total_points = round(self.total_points + new_points, 2)
            return

        # Find the lowest scoring counting competition
        lowest_points = new_points
        lowest_key = new_comp_key

        for comp_key, result in self.competitions.items():
            if result.counts and result.points < lowest_points:
                lowest_points = result.points
                lowest_key = comp_key

        # Drop the lowest score and update total
        if lowest_key != new_comp_key:
            self.competitions[lowest_key].counts = False
            self.total_points = round(self.total_points + new_points - lowest_points, 2)
        else:
            self.competitions[new_comp_key].counts = False

    def to_dict(self):
        return {
            "name": self.name,
            "first_name": self.first_name,
            "gender": self.gender,
            "birth_year": self.birth_year,
            "total_points": self.total_points,
            "nat": self.nat,
            "glider": self.glider,
            "competitions": {k: v.to_dict() for k, v in self.competitions.items()}
        }

    @classmethod
    def from_dict(cls, civl_id: str, data: dict):
        comps = {k: CompetitionResult.from_dict(v) for k, v in data.get("competitions", {}).items()}
        return cls(
            civl_id=civl_id,
            name=data["name"],
            first_name=data["first_name"],
            gender=data["gender"],
            nat=data["nat"],
            glider=data["glider"],
            birth_year=data.get("birth_year", 0),
            total_points=data.get("total_points", 0.0),
            competitions=comps
        )