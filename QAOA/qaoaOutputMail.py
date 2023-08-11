# -*- coding: utf-8 -*-
# zato: ide-deploy=True
import json
import matplotlib.pyplot as plt

import numpy as np

from zato.common import SMTPMessage
from zato.server.service import Service, Model

class QaoaOutputMail(Service):

    name = 'qaoa.qaoa-mail-output'

    def handle(self):
        file = self.request.payload

        f = open(file, 'rb')

        conn = self.email.smtp.get('UMA').conn

        # Create a regular e-mail
        msg = SMTPMessage()
        msg.subject = 'Resultado QAOA'
        msg.to = '0610670999@uma.es'
        msg.from_ = '0610670999@uma.es'

        msg.attach('losses.png', f.read())

        conn.send(msg)

