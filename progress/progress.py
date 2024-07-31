import time


class Progress:
    def __init__(self, total_minutes: int, objectives_count: int):
        self.time_total = total_minutes * 60
        self.time_start = int(time.time())
        self.objectives_count = objectives_count
        self.objectives_completed = 0
        self.total_objective_progress = 0.0
        self.rounds = 0

    def get_round(self):
        return self.rounds

    def get_time_elapsed(self):
        return time.time() - self.time_start

    def get_time_remaining(self):
        return max(0, int(self.time_total - self.get_time_elapsed()))

    def on_interviewee_replied(self, objectives_completed: int, total_objective_progress: float):
        self.rounds += 1
        self.objectives_completed = objectives_completed
        self.total_objective_progress = total_objective_progress

    def get_progress(self):
        assert self.objectives_count > 0
        stats = {
            "round_total": self.rounds,
            "objectives_total": self.objectives_count,
            "objectives_completed_count": self.objectives_completed,
            "objectives_completed": f'{(self.total_objective_progress/self.objectives_count * 100) * 100}%',
            "time_total": int(self.time_total / 60) or 1,
            "time_remaining": int(self.get_time_remaining() / 60)
        }
        if self.rounds == 0:
            stats["average_time_per_round"] = "Unknown"
            stats["rounds_remaining"] = "Unknown"
        else:
            average_time = self.get_time_elapsed() / self.rounds
            if average_time < 60:
                stats["average_time_per_round"] = "小于1"
            else:
                stats["average_time_per_round"]=f"{int(average_time/60)}"
            stats["rounds_remaining"] = f"{int(self.get_time_remaining()/average_time)}"

        return stats
