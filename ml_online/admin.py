from django.contrib import admin
from .models import StudentRealtimeAggregate

@admin.register(StudentRealtimeAggregate)
class StudentRealtimeAggregateAdmin(admin.ModelAdmin):
    list_display = (
        'ml_student_id', 'child', 'updated_at',
        'completion_rate', 'avg_score', 'avg_clicks'
    )
    search_fields = ('ml_student_id', 'child__user__username')
    readonly_fields = ('updated_at',)
    list_filter = ('updated_at',)
