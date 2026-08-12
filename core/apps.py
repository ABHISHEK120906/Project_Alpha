from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import models
import os


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        pass


