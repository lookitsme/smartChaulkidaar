from django import template

register = template.Library()

@register.filter
def range_filter(value):
    return range(1, value + 1)

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})