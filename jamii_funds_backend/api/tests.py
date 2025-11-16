from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from decimal import Decimal

from .models import Member, Chama, Membership, Loan, Contribution, Repayment


class ApiFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chama = Chama.objects.create(name="TestChama")
        self.member = Member.objects.create(
            name="Alice", phone="0712345678", national_id="12345"
        )
        self.membership = Membership.objects.create(
            member=self.member, chama=self.chama, is_admin=True
        )

    def test_create_contribution(self):
        url = reverse("contribution-list")
        data = {"membership": self.membership.id, "amount": "500.00"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)
        c = Contribution.objects.get(id=resp.data["id"])
        self.assertEqual(c.amount, Decimal("500.00"))

    def test_loan_approval_and_repayment(self):
        loan_data = {
            "membership": self.membership.id,
            "principal": "1000.00",
            "interest_rate": "1.50",
            "tenure_months": 2,
        }
        resp = self.client.post(reverse("loan-list"), loan_data, format="json")
        self.assertEqual(resp.status_code, 201)

        loan_id = resp.data["id"]
        resp = self.client.post(reverse("loan-approve", args=[loan_id]), {})
        self.assertEqual(resp.status_code, 200)

        loan = Loan.objects.get(pk=loan_id)
        emi = loan.emi
        repay_data = {
            "loan": loan.id,
            "amount": str((emi * loan.tenure_months).quantize(Decimal("0.01"))),
        }
        resp = self.client.post(reverse("repayment-list"), repay_data)
        self.assertEqual(resp.status_code, 201)
