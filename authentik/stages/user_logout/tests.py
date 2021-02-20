"""logout tests"""
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import User
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.user_logout.forms import UserLogoutStageForm
from authentik.stages.user_logout.models import UserLogoutStage


class TestUserLogoutStage(TestCase):
    """Logout tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-logout",
            slug="test-logout",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = UserLogoutStage.objects.create(name="logout")
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_valid_password(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[
            PLAN_CONTEXT_AUTHENTICATION_BACKEND
        ] = "django.contrib.auth.backends.ModelBackend"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"args": {"to": reverse("authentik_core:shell")}, "type": "redirect"},
        )

    def test_form(self):
        """Test Form"""
        data = {"name": "test"}
        self.assertEqual(UserLogoutStageForm(data).is_valid(), True)
