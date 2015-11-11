def installed(name, **kwargs):
	'''
	'''
	ret = __salt__['splunk.install'](**kwargs)
	changes = {}

	if 0 == ret['retcode']:
		result = True
		comment = "Splunk was installed successfully"
		changes['new'] = "installed"
	else:
		result = False
		comment = "Splunk was not installed: {s}".format(s=ret['stderr'])

	return {'name': name, 'changes': changes,
			'result': result, 'comment': comment}