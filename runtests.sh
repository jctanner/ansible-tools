#!/bin/bash

PYTHONPATH=.:$PYTHONPATH nosetests -v --nocapture tests/
