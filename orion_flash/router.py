"""
.. _router:

django router module for the orion_flash app

forces all data operations to orion_aux (the MS SQL database from where
the Orion server will pick up our alerts

:module:    p_soc_auto.orion_flash.router

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jan. 15, 2019

"""


class OrionAuxRouter():
    """
    database router class for the orion auxiliary database
    """

    def db_for_read(self, model, **hints):
        """
        all models in orion_flash will read from the orion auxiliary database
        """
        if model._meta.app_label == 'orion_flash':
            return 'orion_aux_db'

        return None

    def db_for_write(self, model, **hints):
        """
        all models in orion_flash will write to the orion auxiliary
        database
        """
        if model._meta.app_label == 'orion_flash':
            return 'orion_aux_db'

        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        don't allow cross-database relationships

        we will worry about this later if we have to
        """
        if obj1._state.db == 'orion_aux_db' and obj2._state.db == 'orion_aux_db':
            return True

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        keep the migrations in the orion_aux database
        """
        if app_label == 'orion_flash':
            return db == 'orion_aux_db'

        return None
