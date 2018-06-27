# Standard library imports
import json
import logging

# Third party imports
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

# Local application/library imports
from dojo.models import Rule,\
    System_Settings, Finding, Test, Test_Type, Engagement, \
    Product, Product_Type
from dojo.forms import RuleFormSet, DeleteRuleForm
from dojo.utils import add_breadcrumb

logger = logging.getLogger(__name__)

# Fields for each model ruleset

finding_fields = [f.name for f in Finding._meta.fields]
test_fields = [f.name for f in Test._meta.fields]
test_type_fields = [f.name for f in Test_Type._meta.fields]
engagement_fields = [f.name for f in Engagement._meta.fields]
product_fields = [f.name for f in Product._meta.fields]
product_type_fields = [f.name for f in Product_Type._meta.fields]
field_dictionary = {}
field_dictionary['Finding'] = finding_fields
field_dictionary['Test Type'] = test_type_fields
field_dictionary['Test'] = test_fields
field_dictionary['Engagement'] = engagement_fields
field_dictionary['Product'] = product_fields
field_dictionary['Product Type'] = product_type_fields


def rules(request):
    initial_queryset = Rule.objects.all().order_by('name')
    add_breadcrumb(title="Rules", top_level=True, request=request)
    return render(request, 'dojo/rules.html', {
        'name': 'Rules List',
        'metric': False,
        'user': request.user,
        'rules': initial_queryset})


@user_passes_test(lambda u: u.is_staff)
def new_rule(request):
    if request.method == 'POST':
        form = RuleFormSet(request.POST)
        match_f = request.POST.get('match_field')
        apply_f = request.POST.get('applied_field')
        if form.is_valid():
            form.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 'Rule created successfully.',
                                 extra_tags='alert-success')
            return HttpResponseRedirect(reverse('rules'))
    form = RuleFormSet(queryset=Rule.objects.none())
    add_breadcrumb(title="New Dojo Rule", top_level=False, request=request)
    return render(request, 'dojo/new_rule.html',
                  {'form': form,
                   'finding_fields': finding_fields,
                   'test_fields': test_fields,
                   'engagement_fields': engagement_fields,
                   'product_fields': product_fields,
                   'product_type_fields': product_type_fields,
                   'field_dictionary': json.dumps(field_dictionary)})


@user_passes_test(lambda u: u.is_staff)
def edit_rule(request, pid):
    pt = get_object_or_404(Rule, pk=pid)
    children = Rule.objects.filter(parent_rule=pt)
    all_rules = children | Rule.objects.filter(pk=pid)
    form = RuleFormSet(queryset=all_rules)
    if request.method == 'POST':
        form = RuleFormSet(request.POST)
        if form.is_valid():
            pt = form.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 'Rule updated successfully.',
                                 extra_tags='alert-success')
            return HttpResponseRedirect(reverse('rules'))
    add_breadcrumb(title="Edit Rule", top_level=False, request=request)
    return render(request, 'dojo/edit_rule2.html', {
        'name': 'Edit Rule',
        'metric': False,
        'user': request.user,
        'form': form,
        'field_dictionary': json.dumps(field_dictionary),
        'pt': pt, })


@user_passes_test(lambda u: u.is_staff)
def delete_rule(request, pid):
    product = get_object_or_404(Rule, pk=pid)
    form = DeleteRuleForm(instance=product)

    from django.contrib.admin.utils import NestedObjects
    from django.db import DEFAULT_DB_ALIAS

    collector = NestedObjects(using=DEFAULT_DB_ALIAS)
    collector.collect([product])
    rels = collector.nested()

    if request.method == 'POST':
        if 'id' in request.POST and str(product.id) == request.POST['id']:
            form = DeleteRuleForm(request.POST, instance=product)
            if form.is_valid():
                product.delete()
                messages.add_message(request,
                                     messages.SUCCESS,
                                     'Rule deleted.',
                                     extra_tags='alert-success')
                return HttpResponseRedirect(reverse('Rules'))

    add_breadcrumb(parent=product, title="Delete", top_level=False, request=request)
    system_settings = System_Settings.objects.get()
    return render(request, 'dojo/delete_product.html',
                  {'product': product,
                   'form': form,
                   'active_tab': 'findings',
                   'system_settings': system_settings,
                   'rels': rels,
                   })