# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document

class PropertySetter(Document):
	def autoname(self):
		self.name = self.doc_type + "-" \
			+ (self.field_name and (self.field_name + "-")  or "") \
			+ self.property

	def validate(self):
		"""delete other property setters on this, if this is new"""
		if self.get('__islocal'):
			frappe.db.sql("""delete from `tabProperty Setter` where
				doctype_or_field = %(doctype_or_field)s
				and doc_type = %(doc_type)s
				and ifnull(field_name,'') = ifnull(%(field_name)s, '')
				and property = %(property)s""", self.get_valid_dict())

		# clear cache
		frappe.clear_cache(doctype = self.doc_type)

	def get_property_list(self, dt):
		return frappe.db.sql("""select fieldname, label, fieldtype
		from tabDocField
		where parent=%s
		and fieldtype not in ('Section Break', 'Column Break', 'HTML', 'Read Only', 'Table', 'Fold')
		and ifnull(fieldname, '') != ''
		order by label asc""", dt, as_dict=1)

	def get_setup_data(self):
		return {
			'doctypes': [d[0] for d in frappe.db.sql("select name from tabDocType")],
			'dt_properties': self.get_property_list('DocType'),
			'df_properties': self.get_property_list('DocField')
		}

	def get_field_ids(self):
		return frappe.db.sql("select name, fieldtype, label, fieldname from tabDocField where parent=%s", self.doc_type, as_dict = 1)

	def get_defaults(self):
		if not self.field_name:
			return frappe.db.sql("select * from `tabDocType` where name=%s", self.doc_type, as_dict = 1)[0]
		else:
			return frappe.db.sql("select * from `tabDocField` where fieldname=%s and parent=%s",
				(self.field_name, self.doc_type), as_dict = 1)[0]

	def on_update(self):
		if not getattr(self, "ignore_validate", False):
			from frappe.core.doctype.doctype.doctype import validate_fields_for_doctype
			validate_fields_for_doctype(self.doc_type)

def make_property_setter(doctype, fieldname, property, value, property_type, for_doctype = False, ignore_validate=False):
	# WARNING: Ignores Permissions
	property_setter = frappe.get_doc({
		"doctype":"Property Setter",
		"doctype_or_field": for_doctype and "DocType" or "DocField",
		"doc_type": doctype,
		"field_name": fieldname,
		"property": property,
		"value": value,
		"property_type": property_type
	})
	property_setter.ignore_permissions = True
	property_setter.ignore_validate = ignore_validate
	property_setter.insert()
	return property_setter
