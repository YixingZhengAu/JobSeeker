#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for job recommender functionality
"""

import os
from dotenv import load_dotenv
import config
from job_recommender import recommend_jobs
load_dotenv()

    
# Example user description
description = """
I am a machine learning engineer
"""

# 使用主接口
recommended_jobs = recommend_jobs(
    description=description,
    top_n=3
)

for job in recommended_jobs:
    print(job[0])
    print(job[1])
    print(job[2])
    print("-"*100)