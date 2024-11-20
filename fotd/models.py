import datetime

# from django.contrib.postgres.fields import JSONField # for PostgreSQL
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import JSONField, UniqueConstraint  # for SQLite
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

PHASE_CHOICES = [
    ('Planning', 'Planning'),
    ('Development', 'Development'),
    ('Testing', 'Testing'),
    ('Done', 'Done'),
]

RISK_LEVELS = [
    ('Green', 'Green'),
    ('Yellow', 'Yellow'),
    ('Red', 'Red'),
]

TASK_STATUS = [('ongoing', 'Ongoing'), ('blocked', 'Blocked'), ('closed', 'Closed')]

TEAM_ROLES = [
    ('CFAM Coauthor', 'CFAM Coauthor'),
    ('CFAM Contributor', 'CFAM Contributor'),
    ('FOT Member', 'FOT Member'),
    ('Other Role', 'Other Role'),
]


# Extend the User model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # email = models.EmailField(max_length=255, blank=True) # frank.fang@nokia-sbell.com
    # login_id = models.CharField(max_length=100, blank=True)   # qwn783
    employee_id = models.CharField(max_length=8, blank=True)  # 61403612
    disp_name = models.CharField(max_length=100, blank=True)  # Frank Fang (NSB)
    title = models.CharField(max_length=100, blank=True)  # SW Engineer
    department = models.CharField(max_length=100, blank=True)  # 5G R&D
    country = models.CharField(max_length=100, blank=True)  # China
    created = models.CharField(max_length=20, blank=True)  # 2021-01-01

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()


class ProgramBoundary(models.Model):
    release = models.CharField(max_length=4)
    category = models.CharField(max_length=50)

    sw_done = models.CharField(max_length=4)
    et_ec = models.CharField(max_length=4)
    et_fer = models.CharField(max_length=4)
    et_done = models.CharField(max_length=4)
    st_ec = models.CharField(max_length=4)
    st_fer = models.CharField(max_length=4)
    st_done = models.CharField(max_length=4)
    pet_five_ec = models.CharField(max_length=4)
    pet_five_fer = models.CharField(max_length=4)
    pet_five_done = models.CharField(max_length=4)
    ta = models.CharField(max_length=4)
    cudo = models.CharField(max_length=4)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f'{self.release} - {self.category}: SW {self.sw_done} - ST {self.st_done}'
        )

    class Meta:
        verbose_name_plural = "Program Boundaries"
        constraints = [
            UniqueConstraint(
                fields=['release', 'category'], name='unique_release_category'
            )
        ]


# feature model
class Feature(models.Model):
    id = models.CharField(max_length=11, primary_key=True)
    name = models.CharField(max_length=128)

    release = models.CharField(max_length=20)  # LLF/e-LLF has multiple releases
    priority = models.IntegerField(blank=True, validators=[MaxValueValidator(99999)])

    # Labels like Test_Heavy, LeadTribe_xxx, program milestone, etc.
    labels = models.CharField(blank=True, max_length=100)
    boundary = models.ForeignKey(
        ProgramBoundary, on_delete=models.PROTECT, blank=True, null=True
    )

    phase = models.CharField(max_length=12, choices=PHASE_CHOICES, default='Planning')
    customer = models.CharField(max_length=100, blank=True)
    apm = models.CharField(max_length=100, blank=True)
    fusion_id = models.CharField(max_length=16, blank=True)

    # links
    fp_link = models.CharField(
        max_length=100, blank=True, verbose_name='FP Link', help_text='Link to the FP'
    )
    cfam_link = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='CFAM Link',
        help_text='Link to the CFAM',
    )
    rep_link = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Reporting Portal',
        help_text='Link to the Reporting Portal',
    )

    risk_status = models.CharField(max_length=6, default='Green', choices=RISK_LEVELS)
    risk_summary = models.CharField(max_length=50, blank=True)
    text2_desc = models.CharField(max_length=512, blank=True)
    text2_date = models.DateField(default=datetime.date.today)

    desc = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.release + ' ' + self.id

    class Meta:
        ordering = ["release", 'priority']


# Feature updates
# All manually added updates are key events, while automatically added
# updates (like a task done, risk change) are regular updates
class FeatureUpdate(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    update_date = models.DateField(default=datetime.date.today)
    update_text = models.TextField()
    is_key = models.BooleanField(default=False, verbose_name='Is key event?')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f'{self.feature_id} | '
            f'{self.update_date.strftime("%m/%d")}: '
            f'{self.update_text}'
        )


class FeatureRoles(models.Model):
    feature = models.OneToOneField(
        Feature,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    pdm = models.CharField(max_length=100)
    apm = models.CharField(max_length=100)
    fot_lead = models.CharField(max_length=100)
    cfam_lead = models.CharField(max_length=100)
    lese = models.CharField(max_length=100, blank=True)
    ftl = models.CharField(max_length=100, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s | FOT Lead: %s' % (self.feature_id, self.fot_lead)

    class Meta:
        verbose_name_plural = "FeatureRoles"

    # needless to provide a success_url for CreateView or UpdateView - they will
    # use get_absolute_url() on the model object if available
    def get_absolute_url(self):
        return reverse("fotd:fot", kwargs={"pk": self.pk})


# for cfam_coauthors, cfam_reviewers and fot_members
class TeamMember(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    team = models.CharField(max_length=50)
    apo = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=20, choices=TEAM_ROLES)
    name = models.CharField(max_length=100)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.feature_id} | {self.team} - {self.role}: {self.name}'

    def get_absolute_url(self):
        return reverse("fotd:fot", kwargs={"pk": self.pk})


class Task(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    owner = models.CharField(max_length=20)
    contact = models.CharField(max_length=100, blank=True)
    due = models.DateField()
    status = models.CharField(max_length=11, default='ongoing', choices=TASK_STATUS)
    chat = models.CharField(max_length=50, blank=True)
    mail = models.CharField(max_length=100, blank=True)
    meeting = models.CharField(max_length=100, blank=True)

    # relate_to = models.ForeignKey('self', blank=True, null=True)
    top = models.BooleanField(default=False)  # top task will be shown in homepage
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.feature_id:<13} | {self.title}, due {self.due.strftime("%m/%d")}'


class StatusUpdate(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    update_date = models.DateField(default=datetime.date.today)
    update_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.update_date.strftime("%m/%d")}: {self.update_text}'


# type: process, tool, document/article, etc.
# domain: FOT, CFAM, JIRA, NIDD, IDT, etc.
# description: for searching
class Link(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    category = models.CharField(max_length=25)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # return f'{self.name}: {self.url}'
        return f'[{self.category}] {self.name}'


class Sprint(models.Model):
    fb = models.CharField(max_length=6)
    start_date = models.DateField()
    end_date = models.DateField()
    release = models.CharField(max_length=4, blank=True)
    checkpoint = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return (
            f'{self.fb}: '
            f'{self.start_date.strftime("%m/%d")} - '
            f'{self.end_date.strftime("%m/%d")}'
        )


# Save backlog queries from JIRA
class BacklogQuery(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    query_time = models.DateTimeField(auto_now_add=True)
    query_result = JSONField()
    subfeatures = models.CharField(max_length=9, blank=True)
    display_fields = JSONField()
    start_earliest = models.CharField(max_length=4, blank=True)
    end_latest = models.CharField(max_length=4, blank=True)
    rfc_ratio = models.IntegerField(blank=True)
    committed_ratio = models.IntegerField(blank=True)
    total_spent = models.DecimalField(max_digits=9, decimal_places=2)
    total_remaining = models.DecimalField(max_digits=9, decimal_places=2)
    changes = models.TextField(blank=True)

    class Meta:
        ordering = ['-query_time']
        verbose_name_plural = "Backlog Queries"

    def __str__(self):
        return f'{self.feature_id} | {self.query_time.strftime("%m/%d %H:%M")}'
