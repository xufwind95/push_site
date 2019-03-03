from django.db import models
import uuid


def _upload_to(instance, filename):
    if '/' in filename:
        filename = filename.split('/')[-1]
    return 'data/wallpaper/mp3/{uuid}/{filename}'.format(
        uuid=uuid.uuid4().hex,
        filename=filename
    )


class Wallpaper(models.Model):
    name = models.CharField(max_length=180)
    original_url = models.CharField(max_length=200)
    mp3 = models.FileField(upload_to=_upload_to, max_length=200)

    def __str__(self):
        return "{}".format(self.name)
