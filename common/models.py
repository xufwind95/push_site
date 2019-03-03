import logging

from collections import Counter
from operator import attrgetter

from django.utils import timezone
from django.db import models, router, transaction
from django.db.models import signals, sql, FieldDoesNotExist


class TimestampedModel(models.Model):
    # A timestamp representing when this object was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # A timestamp reprensenting when this object was last updated.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

        # By default, any model that inherits from `TimestampedModel` should
        # be ordered in reverse-chronological order. We can override this on a
        # per-model basis as needed, but reverse-chronological is a good
        # default ordering for most models.
        ordering = ['-created_at', '-updated_at']


class SoftDeleteCollector(models.deletion.Collector):
    def delete(self):
        # sort instance collections
        for model, instances in self.data.items():
            self.data[model] = sorted(instances, key=attrgetter("pk"))

        # if possible, bring the models in an order suitable for databases that
        # don't support transactions or cannot defer constraint checks until the
        # end of a transaction.
        self.sort()
        # number of objects deleted for each model label
        deleted_counter = Counter()

        with transaction.atomic(using=self.using, savepoint=False):
            # send pre_delete signals
            for model, obj in self.instances_with_model():
                if not model._meta.auto_created:
                    signals.pre_delete.send(
                        sender=model, instance=obj, using=self.using
                    )

            # fast deletes
            for qs in self.fast_deletes:
                # count = qs._raw_delete(using=self.using)
                # deleted_counter[qs.model._meta.label] += count
                if len(qs) == 0:
                    continue
                try:
                    qs.update(deleted_at=timezone.now())
                    deleted_counter[qs.model._meta.label] += len(qs)
                except FieldDoesNotExist as e:
                    logging.error(
                        "SoftDelete FieldDoesNotExist ERROR: {}, Query: {}".format(e, qs)
                    )
                    count = qs._raw_delete(using=self.using)
                    deleted_counter[qs.model._meta.label] += count

            # update fields
            for model, instances_for_fieldvalues in self.field_updates.items():
                for (field, value), instances in instances_for_fieldvalues.items():
                    query = sql.UpdateQuery(model)
                    query.update_batch([obj.pk for obj in instances],
                                       {field.name: value}, self.using)

            # reverse instance collections
            for instances in self.data.values():
                instances.reverse()

            # delete instances
            # for model, instances in self.data.items():
            #     query = sql.DeleteQuery(model)
            #     pk_list = [obj.pk for obj in instances]
            #     count = query.delete_batch(pk_list, self.using)
            #     deleted_counter[model._meta.label] += count

            #     if not model._meta.auto_created:
            #         for obj in instances:
            #             signals.post_delete.send(
            #                 sender=model, instance=obj, using=self.using
            #             )
            for model, instances in self.data.items():
                pk_list = [obj.pk for obj in instances]
                if hasattr(model, "deleted_at"):
                    query = sql.UpdateQuery(model)
                    query.update_batch(
                        pk_list,
                        {"deleted_at": timezone.now()},
                        self.using
                    )
                    deleted_counter[model._meta.label] += len(pk_list)
                else:
                    query = sql.DeleteQuery(model)
                    count = query.delete_batch(pk_list, self.using)
                    deleted_counter[model._meta.label] += count

                if not model._meta.auto_created:
                    for obj in instances:
                        signals.post_delete.send(
                            sender=model, instance=obj, using=self.using
                        )

        # update collected instances
        for instances_for_fieldvalues in self.field_updates.values():
            for (field, value), instances in instances_for_fieldvalues.items():
                for obj in instances:
                    setattr(obj, field.attname, value)
        for model, instances in self.data.items():
            for instance in instances:
                setattr(instance, model._meta.pk.attname, None)

        return sum(deleted_counter.values()), dict(deleted_counter)


class SoftDeleteQuerySet(models.QuerySet):

    def delete(self):
        """Delete the records in the current QuerySet."""
        assert self.query.can_filter(), \
            "Cannot use 'limit' or 'offset' with delete."

        if self._fields is not None:
            raise TypeError("Cannot call delete() after .values() or .values_list()")

        del_query = self._chain()

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        del_query._for_write = True

        # Disable non-supported fields.
        del_query.query.select_for_update = False
        del_query.query.select_related = False
        del_query.query.clear_ordering(force_empty=True)

        collector = SoftDeleteCollector(using=del_query.db)
        collector.collect(del_query)
        deleted, _rows_count = collector.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None
        return deleted, _rows_count


class SoftDeleteManager(models.Manager):

    def __init__(self, *args, **kwargs):
        # If deleted_aslo is True, then we return all objects,
        # including soft deleted objects.
        self.deleted_also = kwargs.pop('deleted_aslo', False)

        super(SoftDeleteManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.deleted_also:
            return SoftDeleteQuerySet(self.model)

        return SoftDeleteQuerySet(self.model).filter(deleted_at=None)


class SoftDeleteModel(TimestampedModel):
    deleted_at = models.DateTimeField(default=None, null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager(deleted_aslo=True)

    def delete(self, using=None, keep_parents=False):
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self.pk is not None, (
            "%s object can't be deleted because its %s attribute is set to None." %
            (self._meta.object_name, self._meta.pk.attname)
        )

        collector = SoftDeleteCollector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()

    class Meta:
        abstract = True
