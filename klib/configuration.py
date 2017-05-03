class Configurator:

    def __init__(self, conf_options):
        self.conf_options = conf_options

    def boot(self):
        if 'boot' in self.conf_options:
            return self.conf_options['boot']
        else:
            raise Exception("Invalid config option requested: {}".
                            format('boot'))

    def roles(self):
        if 'roles' in self.conf_options:
            return self.conf_options['roles']
        else:
            raise Exception("Invalid config option requested: {}".
                            format('roles'))

    def client(self):
        if 'client' in self.conf_options:
            return self.conf_options['client']
        else:
            raise Exception("Invalid config option requested: {}".
                            format('client'))

    def server(self):
        if 'server' in self.conf_options:
            return self.conf_options['server']
        else:
            raise Exception("Invalid config option requested: {}".
                            format('server'))

    def github(self):
        if 'github' in self.conf_options:
            return self.conf_options['github']
        else:
            raise Exception("Invalid config option requested: {}".
                            format('github'))
