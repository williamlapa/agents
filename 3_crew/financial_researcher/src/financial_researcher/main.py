#!/usr/bin/env python
# src/financial_researcher/main.py
import os
#from financial_researcher.crew import ResearchCrew
from financial_researcher import ResearchCrew

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def run():
    """
    Run the research crew.
    """
    inputs = {
        'company': 'Applovin Corp',
    }
    company_name = inputs['company']

    # Create and run the crew
    research_crew = ResearchCrew(company=company_name)
    #result = ResearchCrew().crew().kickoff(inputs=inputs)
    result = research_crew.crew().kickoff(inputs=inputs)

    # Print the result
    print("\n\n=== FINAL REPORT ===\n\n")
    print(result.raw)

    print("\n\nReport has been saved to output/report.md")

if __name__ == "__main__":
    run()