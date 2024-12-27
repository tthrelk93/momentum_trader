import pandas as pd

def suggest_portfolio(results, total_portfolio_value):
    allocations = []
    for result in results[:5]:  # Top 5 performers
        weight = result['Final_Balance'] / sum(r['Final_Balance'] for r in results[:5])
        allocations.append({
            'Ticker': result['Ticker'],
            'Weight': weight,
            'Allocation': weight * total_portfolio_value
        })
    return allocations

