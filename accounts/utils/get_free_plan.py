from accounts.models import Plan
from typing import Optional

def get_free_plan() -> Optional[Plan]:
    free = Plan.objects.filter(name__iexact="free").first()
    if free:
        return free
    return Plan.objects.filter(requires_payment=False, is_plan_staff=False).first()
