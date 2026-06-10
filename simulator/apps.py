from django.apps import AppConfig

class SimulatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simulator'
    
    def ready(self):
        """Register signals when app is ready"""
        import os
        if not os.environ.get('DISABLE_SIGNALS'):
            import simulator.signals  # This will register the signal handlers
            import simulator.workspace_signals  # ensure user workspace clone on login
        from simulator.admin_roles import connect_admin_role_groups
        connect_admin_role_groups(self)
