from django.db import models
from django.core.validators import MaxValueValidator
import datetime

MILESTONE_CHOICES = [
    ('N/A',    'N/A'),
    ('I1 50%',    'I1 50%'),
    ('I1',        'I1'),
    ('I1.1',      'I1.1'),
    ('I1.2',      'I1.2'),
    ('P2',        'P2'),
    ('Post P2',   'Post P2'),
]

PHASE_CHOICES = [
    ('Planning',  'Planning'),
    ('Development','Development'),
    ('Testing',   'Testing'),
    ('Done',      'Done'),
]

RISK_LEVELS = [
    ('Green', 'Green'),
    ('Yellow', 'Yellow'),
    ('Red', 'Red'),
]

TASK_STATUS = [
    ('Not Started', 'Not Started'),
    ('Ongoing', 'Ongoing'),
    ('On Hold', 'On Hold'),
    ('Blocked', 'Blocked'),
    ('Cancelled', 'Cancelled'),
    ('Completed', 'Completed')
]

TEAM_ROLES = [
    ('CFAM Coauthor', 'CFAM Coauthor'),
    ('CFAM Contributor', 'CFAM Contributor'),
    ('FOT Member', 'FOT Member'),
    ('Other Role', 'Other Role'),
]

# feature model
class Feature(models.Model):
    id = models.CharField(max_length=11, primary_key=True)
    name = models.CharField(max_length=100)

    release = models.CharField(max_length=20)    #LLF/e-LLF has multiple releases
    priority = models.IntegerField(validators=[MaxValueValidator(99999)])
    milestone = models.CharField(max_length=7, choices=MILESTONE_CHOICES)
    #labels = models.CharField(max_length=100)  #Test_Heavy, LeadTribe_xxx, etc.
    phase = models.CharField(max_length=12, choices=PHASE_CHOICES, default='Planning')

    # links
    fusion_link = models.CharField(max_length=300, verbose_name='JIRA Structure', help_text='Link to the JIRA Structure')
    fp_link = models.CharField(max_length=100, blank=True, verbose_name='FP Link', help_text='Link to the FP')
    cfam_link = models.CharField(max_length=100, blank=True, verbose_name='CFAM Link', help_text='Link to the CFAM')
    gantt_link = models.CharField(max_length=100, blank=True, verbose_name='Gantt Chart', help_text='Link to the Gantt Chart')
    rep_link = models.CharField(max_length=100, blank=True, verbose_name='Reporting Portal', help_text='Link to the Reporting Portal')
    
    risk = models.CharField(max_length=6, default='Green', choices=RISK_LEVELS)
    text2 = models.CharField(max_length=512, blank=True)
    desc = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.release + ' ' + self.id
    class Meta:
        ordering = ["release", 'priority']

# Feature updates
# All manually added updates are key events, while automatically added updates (like a task done, risk change) are regular updates
class FeatureUpdate(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    update_date = models.DateField(default=datetime.date.today)
    update_text = models.TextField()
    is_key = models.BooleanField(default=False, verbose_name='Is key event?')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.feature_id} | {self.update_date.strftime("%m/%d")}: {self.update_text}'

class FeatureRoles(models.Model):
    feature = models.OneToOneField(Feature, on_delete=models.CASCADE, primary_key=True,)
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

# for cfam_coauthors, cfam_reviewers and fot_members
class TeamMember(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    team = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=TEAM_ROLES)
    name = models.CharField(max_length=100)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.feature_id} | {self.team} - {self.role}: {self.name}'

class Task(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    owner = models.CharField(max_length=20)
    contact = models.CharField(max_length=100, blank=True)
    due = models.DateField(default=datetime.date.today() + datetime.timedelta(days=7))
    status = models.CharField(max_length=11, default='Ongoing', choices=TASK_STATUS)
    mail = models.CharField(max_length=50, blank=True)
    chat = models.CharField(max_length=50, blank=True)
    meeting = models.CharField(max_length=50, blank=True)
    
    relate_to = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.feature_id} | {self.title} - {self.owner}, due {self.due.strftime("%m/%d")}'

class StatusUpdate(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    update_date = models.DateField(default=datetime.date.today)
    update_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.update_date.strftime("%m/%d")}: {self.update_text}'

class Link(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    category = models.CharField(max_length=25)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        #return f'{self.name}: {self.url}'
        return f'<a href="{self.url}">{self.name}</a>'

class Sprint(models.Model):
    fb = models.CharField(max_length=6)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f'{self.fb}: {self.start_date.strftime("%m/%d")} - {self.end_date.strftime("%m/%d")}'
