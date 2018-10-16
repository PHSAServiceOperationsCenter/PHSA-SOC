"""
.. _tasks:

celery tasks for the rules_engine app

:module:    p_soc_auto.rules_engine.tasks

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Sep. 5, 2018

"""
from django.utils import timezone
from celery import shared_task, group

from .models import RegexRule, IntervalRule, ExpirationRule


@shared_task(
    task_serializer='pickle', result_serializer='pickle', rate_limit='30/s',
    queue='rules')
def apply_rule(rule):
    """
    celery task wrapper for the overloaded
    :method:`rules_engine.models.Rule.apply_rule`

    note that we need to force the use of the pickle serializer because
    this task is putting django queryset objects (that cannot be serialized
    with JSON) on the wire; this may present security risks on an open network

    :arg rule: a rule object

    :returns: the name and instance type of the rule
    """
    rule.apply_rule()
    return 'applied rule {}.{}'.format(
        rule._meta.verbose_name_plural, rule.rule)


@shared_task(queue='shared')
def apply_intervals():
    """
    task wrapper for executing all the tasks in the group associated with
    :class:`rules_engine.models.IntervalRule`

    this could be extended for more than one rule type but creating tasks
    or groups of tasks will become more and more complex

    """
    group(apply_rule.s(rule).set(serializer='pickle') for
          rule in IntervalRule.objects.filter(enabled=True).all())()

    return '{}: bootstrapped interval rules'.format(timezone.now())


@shared_task(queue='shared')
def apply_expiration():
    """
    task wrapper for executing all the tasks in the group associated with
    :class:`rules_engine.models.ExpirationRule`
    """
    group(apply_rule.s(rule).set(serializer='pickle') for
          rule in ExpirationRule.objects.filter(enabled=True).all())()

    return '{}: bootstrapped expiration rules'.format(timezone.now())


@shared_task(queue='shared')
def apply_regex_rules():
    """
    task wrapper for executing all the tasks in the group associated with
    :class:`rules_engine.models.ExpirationRule`
    """
    group(apply_rule.s(rule).set(serializer='pickle') for
          rule in RegexRule.objects.filter(enabled=True).all())()

    return '{}: bootstrapped regex rules'.format(timezone.now())
