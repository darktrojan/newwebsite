from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from content.models import MenuEntry

register = template.Library()


@register.simple_tag(takes_context=True)
def menu(context, max_depth=None):
	path = context['request'].path

	def list_formatter(item_list, depth=1):
		if len(item_list) == 0 or (max_depth is not None and depth > max_depth):
			return ''

		output = [
			'<ul data-depth="%d">' % depth
		]
		for item in item_list:
			classes = []
			text = conditional_escape(item.label)

			if item.href:
				if item.href.rstrip('/') == path.rstrip('/'):
					classes.append('current')
				elif path.startswith(item.href):
					prefix = True
					path_parts = path.split('/')
					href_parts = item.href.split('/')
					for i in range(0, len(href_parts)):
						if path_parts[i] != href_parts[i]:
							prefix = False
							break
					if prefix:
						classes.append('prefix')

				tag = '<a href="%s">%s</a>' % (item.href, text)
			else:
				tag = '<span>%s</span>' % text
			sublist = list_formatter(item.get_children(), depth + 1)

			if not item.is_leaf_node():
				classes.append('has_children')
			if current and item.is_ancestor_of(current):
				classes.append('ancestor')
			if current and item.is_descendant_of(current):
				classes.append('descendant')
			output.append('<li class="%s">%s%s</li>' % (' '.join(classes), tag, sublist))
		output.append('</ul>')
		return ''.join(output)

	try:
		current = MenuEntry.objects.get(href=path)
	except MenuEntry.DoesNotExist:
		current = None
	return mark_safe(list_formatter(MenuEntry.objects.root_nodes()))
