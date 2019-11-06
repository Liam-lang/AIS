#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 16, 2018
rdgenerator.py: random string generator for filename change.
@author: Neo
Version: 1.0
'''
import string, random


def id_generator(size=6, chars=string.ascii_letters + string.digits):
    rd = ''.join(random.choice(chars) for _ in range(size))
    return rd
