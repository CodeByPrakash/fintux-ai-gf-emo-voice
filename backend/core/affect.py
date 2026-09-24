import time


class AffectModel:
    """Tracks FENRY's mood, energy, and attachment over conversations."""

    def __init__(self):
        self.mood = 0.7
        self.energy = 0.8
        self.attachment = 0.5
        self._history = []

    def update(self, user_message: str, fenry_response: str = ""):
        positive = ["thank", "love", "happy", "great", "awesome", "good",
                     "amazing", "miss you", "cute", "beautiful", "lol", "haha",
                     "\u2764", "\ud83d\ude0a", "\ud83e\udd70", "\ud83d\ude18", "\ud83d\ude0d"]
        negative = ["sad", "angry", "upset", "hate", "bad", "tired",
                     "annoyed", "frustrated", "bye", "leave",
                     "\ud83d\ude22", "\ud83d\ude21"]

        msg_lower = user_message.lower()

        pos_count = sum(1 for w in positive if w in msg_lower)
        neg_count = sum(1 for w in negative if w in msg_lower)

        if pos_count > neg_count:
            self.mood = min(1.0, self.mood + 0.05 * pos_count)
            self.energy = min(1.0, self.energy + 0.03)
        elif neg_count > pos_count:
            self.mood = max(0.0, self.mood - 0.03 * neg_count)

        self.attachment = min(1.0, self.attachment + 0.02)
        self.energy = max(0.3, self.energy - 0.01)

        self.mood = round(max(0, min(1, self.mood)), 3)
        self.energy = round(max(0, min(1, self.energy)), 3)
        self.attachment = round(max(0, min(1, self.attachment)), 3)

        self._history.append({
            "mood": self.mood,
            "energy": self.energy,
            "attachment": self.attachment,
            "timestamp": time.time()
        })

    def get_state(self) -> dict:
        return {"mood": self.mood, "energy": self.energy, "attachment": self.attachment}

    def get_history(self, limit: int = 50) -> list:
        return self._history[-limit:]

    def get_mood_descriptor(self) -> str:
        if self.mood > 0.8:
            return "very happy and affectionate"
        elif self.mood > 0.6:
            return "warm and cheerful"
        elif self.mood > 0.4:
            return "calm and neutral"
        elif self.mood > 0.2:
            return "a bit quiet and reflective"
        return "subdued and gentle"

    def get_energy_descriptor(self) -> str:
        if self.energy > 0.7:
            return "energetic and enthusiastic"
        elif self.energy > 0.4:
            return "relaxed"
        return "sleepy and mellow"


affect_model = AffectModel()
