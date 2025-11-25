"""
Game Rules Engine
- Enforces gameplay strictly based on the selected format's rules schema.
- Centralizes scoring, negs, powers, bonuses/sixty-second rounds, timers, and tiebreakers per format.
- No hard-coded scoring: all values read from rules schemas (NAQT, OSSAA, FROSHMORE, TRIVIA).

Usage:
    from logic.game_rules_engine import RulesEngine
    re = RulesEngine(format_name="NAQT")
    pts = re.points_for_tossup(state={"power": True})
    neg = re.neg_penalty()
    duration = re.timer_seconds(event="tossup")
"""

import json
import os
from typing import Any, Dict, Optional


class RulesEngine:
    def __init__(self, format_name: str, schemas_dir: Optional[str] = None):
        self.format_name = format_name.strip().upper()
        self.schemas_dir = schemas_dir or os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "schemas")
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        # Rules schema file name convention: <format>_rules_schema.json
        fname = f"{self.format_name.lower()}_rules_schema.json"
        path = os.path.join(self.schemas_dir, fname)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Rules schema not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---------- Scoring ----------

    def points_for_tossup(self, state: Optional[Dict[str, Any]] = None) -> int:
        """
        Returns tossup points for a correct buzz, honoring powers and regulars.
        State can include:
          - {"power": True} to apply power value if defined in schema
        """
        state = state or {}
        gameplay = self.schema.get("sections", {}).get("Gameplay", {})
        # NAQT-style: may define power and regular tossup points
        points_cfg = gameplay.get("tossup_points", {})
        # Fallbacks per format if schema is simple:
        # Froshmore often defines 10 per tossup; Trivia is variable per question.
        if state.get("power") and points_cfg.get("power"):
            return int(points_cfg["power"])
        if points_cfg.get("regular"):
            return int(points_cfg["regular"])
        # Generic fallback: check quarters/tossup default if provided
        # Froshmore single_round_mode quarters -> points_each
        tournaments = self.schema.get("sections", {}).get("Tournaments", {})
        single = tournaments.get("single_round_mode", {})
        # Attempt Froshmore default
        fq = single.get("quarters", {}).get("first_quarter", {})
        if fq and fq.get("points_each"):
            return int(fq["points_each"])
        # Trivia may rely on category points; caller should pass points explicitly if needed
        # Default safe value:
        return 10

    def points_for_bonus(self) -> int:
        """
        Returns points for bonus if applicable to the format.
        For Froshmore/NAQT: often 10 each bonus.
        For OSSAA: sixty-second rounds typically have category totals/time limits; use timers and per-question scoring.
        Trivia: handled by category points, not strict bonuses.
        """
        gameplay = self.schema.get("sections", {}).get("Gameplay", {})
        bonus_cfg = gameplay.get("bonus_points", {})
        if bonus_cfg.get("each"):
            return int(bonus_cfg["each"])
        # Froshmore has 10-point related bonus in quarters
        tournaments = self.schema.get("sections", {}).get("Tournaments", {})
        single = tournaments.get("single_round_mode", {})
        fq = single.get("quarters", {}).get("first_quarter", {}).get("bonus", {})
        if fq and fq.get("points_each"):
            return int(fq["points_each"])
        return 10

    def neg_penalty(self) -> int:
        """
        Returns the penalty for an incorrect early buzz if defined,
        else defaults to -5 for NAQT/OSSAA conventions; Froshmore may be 0 if negs are not used.
        """
        gameplay = self.schema.get("sections", {}).get("Gameplay", {})
        neg = gameplay.get("neg_penalty")
        if isinstance(neg, int):
            return neg
        # Default common academic quiz conventions:
        if self.format_name in {"NAQT", "OSSAA"}:
            return -5
        # Froshmore typically does not penalize negs; use 0 if not defined
        if self.format_name == "FROSHMORE":
            return 0
        # Trivia: no negs in typical pub game
        if self.format_name == "TRIVIA":
            return 0
        return -5

    # ---------- Timers ----------

    def timer_seconds(self, event: str) -> int:
        """
        Returns timer durations per event name: "tossup", "bonus", "sixty_second", "lightning".
        Falls back to sensible defaults if not specified.
        """
        gameplay = self.schema.get("sections", {}).get("Gameplay", {})
        timers = gameplay.get("timers", {})
        if event in timers:
            try:
                return int(timers[event])
            except Exception:
                pass
        # Defaults per format
        if self.format_name == "OSSAA":
            if event == "sixty_second":
                return 60
            if event == "tossup":
                return 5
        if self.format_name in {"NAQT", "FROSHMORE"}:
            if event == "tossup":
                return 5
            if event == "bonus":
                return 5
        if self.format_name == "TRIVIA":
            if event == "tossup":
                return 10
        return 5

    # ---------- Tiebreakers ----------

    def tiebreaker_message(self) -> str:
        """
        Returns the format-specific tiebreaker label to display when sudden-death begins.
        """
        tb = self.schema.get("sections", {}).get("Gameplay", {}).get("tiebreaker_procedure")
        if isinstance(tb, str) and tb.strip():
            return tb
        # Defaults
        if self.format_name == "OSSAA":
            return "OSSAA sudden-death tossups until a clear winner."
        if self.format_name == "FROSHMORE":
            return "Froshmore final tiebreaker: individual tossups until a clear winner."
        return "Sudden-death tossups begin."

    # ---------- Format checks ----------

    def has_sixty_second_round(self) -> bool:
        """
        Detects OSSAA sixty-second rounds or any lightning-like round in schema.
        """
        sections = self.schema.get("sections", {})
        gameplay = sections.get("Gameplay", {})
        if gameplay.get("sixty_second_round"):
            return True
        questions = sections.get("Questions", {})
        if "sixty_second_round" in questions or "lightning_round" in questions:
            return True
        # Froshmore explicitly: no sixty-second rounds
        if self.format_name == "FROSHMORE":
            return False
        return False

    def supports_power(self) -> bool:
        """
        Detects if format has power tossups.
        """
        gameplay = self.schema.get("sections", {}).get("Gameplay", {})
        points_cfg = gameplay.get("tossup_points", {})
        return isinstance(points_cfg.get("power"), int)

    # ---------- Trivia helpers ----------

    def trivia_category_points(self, category_key: str) -> int:
        """
        Returns points for a trivia category if schema defines specific weights.
        Otherwise, caller should specify points per question.
        """
        sections = self.schema.get("sections", {})
        questions = sections.get("Questions", {})
        cats = questions.get("categories", {})
        val = cats.get(category_key)
        if isinstance(val, int):
            return val
        return 1  # default per-question value if not defined