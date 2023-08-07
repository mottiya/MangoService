from datetime import datetime
from django.db import models
from django.forms import model_to_dict
from django.dispatch import receiver


class Advert(models.Model):
    user_name = models.CharField(default='User')
    advert_name = models.CharField(default='Advert')
    link = models.CharField()
    id_avito = models.CharField(max_length=20)
    post_time = models.DateTimeField()
    address = models.CharField(default='Adress')
    detailing = models.TextField(default='Detailing')
    tel = models.CharField(max_length=20)
    source = models.CharField(default='Rest')
    create_time = models.DateTimeField(auto_now_add=True)
    task_id = models.IntegerField(default=None, null=True)

    def __str__(self) -> str:
        return self.id_avito + ": " + self.advert_name

class Caller(models.Model):
    extension = models.CharField(blank=True, null=True)
    number = models.CharField(blank=True, null=True)
    taken_from_call_id = models.CharField(blank=True, null=True)
    line_number = models.CharField(blank=True, null=True)
    acd_group = models.CharField(blank=True, null=True)
    was_transferred = models.BooleanField(default=False)
    hold_initiator = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return model_to_dict(self)

class Call(models.Model):
    entry_id = models.CharField()
    call_id = models.CharField()
    timestamp = models.IntegerField()
    seq = models.IntegerField()
    call_state = models.CharField()
    location = models.CharField()
    from_user = models.OneToOneField(Caller, on_delete=models.PROTECT, related_name='from_user', name='from_user', verbose_name='from_user')
    to_user = models.OneToOneField(Caller, on_delete=models.PROTECT, related_name='to_user', name='to_user', verbose_name='to_user')
    disconnect_reason = models.IntegerField(blank=True, null=True)
    transfer = models.CharField(blank=True, null=True)
    sip_call_id = models.CharField(blank=True, null=True)
    command_id = models.CharField(blank=True, null=True)
    task_id = models.CharField(blank=True, null=True)
    callback_initiator = models.CharField(blank=True, null=True)
    send_flag = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return model_to_dict(self)

class TgNotifier(models.Model):
    tg_id = models.CharField()
    massage = models.TextField()
    post_time = models.DateTimeField(null=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    send_flag = models.BooleanField(default=False)

    def __str__(self) -> str:
        return model_to_dict(self)

# class SimpleSaveTask(models.Model):
#     save_request = models.TextField()
#     create_time = models.DateTimeField(auto_now_add=True)
#     call_initiator = models.ForeignKey(to=Call, on_delete=models.CASCADE)

@receiver(models.signals.post_delete, sender=Call)
def handle_deleted_profile(sender, instance, **kwargs):
    if instance.from_user:
        instance.from_user.delete()
    if instance.to_user:
        instance.to_user.delete()

@receiver
def dj_iter(gen):
    try:
        return next(gen)
    except StopIteration:
        return 'Completed Iteration'