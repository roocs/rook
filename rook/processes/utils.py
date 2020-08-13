def translate_args(request):
    """
    Returns a dictionary of arguments converted from WPS input types
    to python types.

    :param request: WPS request
    :return: Dictionary of converted arguments
    """
    translated = {}

    if 'time' in request.inputs:
        value = request.inputs['time'][0].data
        translated['time'] = value.split('/')

    if 'area' in request.inputs:
        value = request.inputs['area'][0].data
        translated['area'] = [float(item) for item in value.split(',')]

    if 'level' in request.inputs:
        translated['level'] = [item.data for item in request.inputs['level']]

    return translated
