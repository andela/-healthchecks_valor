from django.core import mail
from django.contrib.auth.models import User

from hc.test import BaseTestCase
from hc.accounts.models import Profile, Member
from hc.api.models import Check


class ProfileTestCase(BaseTestCase):

    def test_it_sends_set_password_link(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"set_password": "1"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 302

        # profile.token should be set now
        self.alice.profile.refresh_from_db()
        token = self.alice.profile.token

        ### Assert that the token is set
        self.assertTrue(len(token)>0)

        ### Assert that the email was sent and check email content
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Set password on healthchecks.io", mail.outbox[0].subject)
        self.assertIn("Here's a link to set a password for your account on healthchecks.io:", mail.outbox[0].body)

    def test_it_sends_daily_report(self):
        self.alice.profile.reports_allowed = '1'
        self.alice.profile.save()

        check = Check(name="Test Check", user=self.alice)
        check.save()

        self.alice.profile.send_report()
        ###Assert that the email was sent and check email content
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual('HealthChecks Report', mail.outbox[0].subject)
        self.assertIn('Hello,\n\nThis is a Daily report sent by healthchecks.io', mail.outbox[0].body)

    def test_it_sends_weekly_report(self):
        self.alice.profile.reports_allowed = '2'
        self.alice.profile.save()

        check = Check(name="Test Check", user=self.alice)
        check.save()

        self.alice.profile.send_report()

        ###Assert that the email was sent and check email content
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual('HealthChecks Report', mail.outbox[0].subject)
        self.assertIn('Hello,\n\nThis is a Weekly report sent by healthchecks.io', mail.outbox[0].body)

    def test_it_sends_monthly_report(self):
        self.alice.profile.reports_allowed = '3'
        self.alice.profile.save()

        check = Check(name="Test Check", user=self.alice)
        check.save()

        self.alice.profile.send_report()

        ###Assert that the email was sent and check email content
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual('HealthChecks Report', mail.outbox[0].subject)
        self.assertIn('Hello,\n\nThis is a Monthly report sent by healthchecks.io', mail.outbox[0].body)

    def test_it_adds_team_member(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"invite_team_member": "1", "email": "frank@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        member_emails = set()
        for member in self.alice.profile.member_set.all():
            member_emails.add(member.user.email)

        ### Assert the existence of the member emails
        self.assertIsNotNone(member_emails)

        self.assertTrue("frank@example.org" in member_emails)

        ###Assert that the email was sent and check email content
        self.assertEqual(len(mail.outbox), 1)

        self.assertIn('You have been invited to join alice@example.org on healthchecks.io', mail.outbox[0].subject)
        self.assertIn('Hello,\n\nalice@example.org invites you to their healthchecks.io account.\n\nYou will be able to manage their existing monitoring checks and set up new\nones. If you already have your own account on healthchecks.io, you will\nbe able to switch between the two accounts.\nTo log into healthchecks.io, please open the link below:', mail.outbox[0].body)

    def test_add_team_member_checks_team_access_allowed_flag(self):
        self.client.login(username="charlie@example.org", password="password")

        form = {"invite_team_member": "1", "email": "frank@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 403

    def test_it_removes_team_member(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"remove_team_member": "1", "email": "bob@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        self.assertEqual(Member.objects.count(), 0)

        self.bobs_profile.refresh_from_db()
        self.assertEqual(self.bobs_profile.current_team, None)

    def test_it_sets_team_name(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"set_team_name": "1", "team_name": "Alpha Team"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.team_name, "Alpha Team")

    def test_set_team_name_checks_team_access_allowed_flag(self):
        self.client.login(username="charlie@example.org", password="password")

        form = {"set_team_name": "1", "team_name": "Charlies Team"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 403

    def test_it_switches_to_own_team(self):
        self.client.login(username="bob@example.org", password="password")

        self.client.get("/accounts/profile/")

        # After visiting the profile page, team should be switched back
        # to user's default team.
        self.bobs_profile.refresh_from_db()
        self.assertEqual(self.bobs_profile.current_team, self.bobs_profile)

    def test_it_shows_badges(self):
        self.client.login(username="alice@example.org", password="password")
        Check.objects.create(user=self.alice, tags="foo a-B_1  baz@")
        Check.objects.create(user=self.bob, tags="bobs-tag")

        r = self.client.get("/accounts/profile/")
        self.assertContains(r, "foo.svg")
        self.assertContains(r, "a-B_1.svg")

        # Expect badge URLs only for tags that match \w+
        self.assertNotContains(r, "baz@.svg")

        # Expect only Alice's tags
        self.assertNotContains(r, "bobs-tag.svg")

    ### Test it creates and revokes API key
    def test_it_creates_api_key(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"create_api_key": ""}
        response = self.client.post("/accounts/profile/", form)
        assert response.status_code == 200

        self.alice.profile.refresh_from_db()

    def test_it_revokes_api_key(self):
        self.client.login(username="alice@example.org", password="password")
        
        form = {"revoke_api_key": ""}
        response = self.client.post("/accounts/profile/", form)
        assert response.status_code == 200
    
