 ct=ContentType.objects.get(model='tindataforruledemos')
 
 ct.get_all_objects_for_this_type().first()
 
 ct.get_all_objects_for_this_type().first()._meta.get_fields()


[field.name for field in ct.get_all_objects_for_this_type().first(
)._meta.get_fields() if not field.primary_key and not field.is_relation]
