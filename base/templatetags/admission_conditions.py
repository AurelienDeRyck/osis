from django import template

register = template.Library()


@register.inclusion_tag('templatetags/admission_condition_table_row.html')
def render_condition_rows(section_name, header_text, records):
    return {
        'section_name': section_name,
        'header_text': header_text,
        'records': records,
    }


@register.inclusion_tag('templatetags/admission_condition_text.html')
def render_condition_text(section_name, text, field):
    return {
        'section': section_name,
        'text': text,
        'field': field,
    }
