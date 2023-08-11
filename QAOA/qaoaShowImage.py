# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from zato.server.service import Service

class QaoaShowImage(Service):

    name = 'qaoa.qaoa-show-image'

    def handle(self):
        file = self.request.payload

        result = self.commands.invoke('eog ' + file)

        self.response.payload = result.exit_code
