import importlib


def get_additional_services(settings_module):
    """
        if HENDRIX_SERVICES is specified in settings_module,
        it should be a list twisted internet services

        example:

            HENDRIX_SERVICES = (
              ('myServiceName', 'apps.offload.services.TimeService'),
            )
    """

    additional_services = []

    if hasattr(settings_module, 'HENDRIX_SERVICES'):
        for name, module_path in settings_module.HENDRIX_SERVICES:
            path_to_module, service_name = module_path.rsplit('.', 1)
            resource_module = importlib.import_module(path_to_module)
            additional_services.append(
                (name, getattr(resource_module, service_name))
            )
    return additional_services


def get_additional_resources(settings_module):
    """
    if HENDRIX_CHILD_RESOURCES is specified in settings_module,
    it should be a list resources subclassed from hendrix.contrib.NamedResource

    example:

        HENDRIX_CHILD_RESOURCES = (
          'apps.offload.resources.LongRunningProcessResource',
          'apps.chat.resources.ChatResource',
        )
    """

    additional_resources = []

    if hasattr(settings_module, 'HENDRIX_CHILD_RESOURCES'):
        for module_path in settings_module.HENDRIX_CHILD_RESOURCES:
            path_to_module, resource_name = module_path.rsplit('.', 1)
            resource_module = importlib.import_module(path_to_module)

            additional_resources.append(
                getattr(resource_module, resource_name)
            )

    return additional_resources
