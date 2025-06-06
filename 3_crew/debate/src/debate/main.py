#!/usr/bin/env python
import sys
import warnings
from crew import Debate
#from debate.crew import Debate - deu erro de importação circular

from datetime import datetime

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        #'motion': 'There needs to be strict laws to regulate LLMs',
        'motion': 'A regulamentação legal das redes sociais no Brasil é necessária e urgente. Responda em português.',
    }
    
    try:
        result = Debate().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


if __name__ == "__main__":
    run()