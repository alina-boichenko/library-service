from rest_framework import routers
from payment.views import CreateCheckoutSessionView

router = routers.DefaultRouter()
router.register("payments", CreateCheckoutSessionView)

urlpatterns = router.urls

app_name = "payment"
