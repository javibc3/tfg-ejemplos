# -*- coding: utf-8 -*-
# zato: ide-deploy=True
import json
import matplotlib.pyplot as plt

from zato.server.service import Service

class QaoaCreateImage(Service):

    name = 'qaoa.qaoa-create-image'

    def handle(self):
        losses = json.loads(self.request.payload)
        plt.plot(losses, "-o")
        plt.ylabel("Cost")
        plt.xlabel("Iteration")
        plt.title("QAOA convergence of cost function")
        plt.savefig('losses.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.invoke_async('qaoa.qaoa-mail-output', 'losses.png')
        self.invoke_async('qaoa.qaoa-show-image', 'losses.png')