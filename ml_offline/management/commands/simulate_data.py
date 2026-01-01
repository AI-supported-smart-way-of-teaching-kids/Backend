from django.core.management.base import BaseCommand
from ml_offline.models import LessonInteractionsRaw
from ml_online.models import StudentRealtimeAggregate
import secrets


class Command(BaseCommand):
    help = "Simulates a student taking lessons to test the ML pipeline"

    def handle(self, *args, **kwargs):
        student_id = 1
        self.stdout.write(
            self.style.SUCCESS(f"--- Starting Simulation for Student {student_id} ---")
        )

        # 1. Create 5 fake raw lesson interactions
        for i in range(1, 6):
            # generate a secure pseudo-random float between 5.0 and 20.0 using milliseconds
            ms = secrets.randbelow(15001)  # 0..15000 -> 5.000..20.000
            time_spent = 5.0 + ms / 1000.0
            LessonInteractionsRaw.objects.create(
                ml_student_id=student_id,
                lesson_id=100 + i,
                time_spent=time_spent,
                video_watch_percentage=secrets.randbelow(51) + 50,  # 50..100
                number_of_clicks=secrets.randbelow(41) + 10,  # 10..50
                completion_status=True,
            )
            self.stdout.write(f"Logged Lesson {100+i}: Spent {time_spent:.2f} mins")

        # 2. Check the "Online" result (This proves the Signal worked!)
        agg = StudentRealtimeAggregate.objects.get(ml_student_id=student_id)

        # FIXED LINES BELOW: Removed the 'f' from strings without placeholders
        self.stdout.write(self.style.SUCCESS("--- Result in Online Table ---"))
        self.stdout.write(f"Average Time Calculated: {agg.avg_time_spent:.2f} mins")
        self.stdout.write(f"Total Lessons Tracked: {agg.lessons_completed}")
        self.stdout.write(self.style.SUCCESS("--- Pipeline Test Complete! ---"))
