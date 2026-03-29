from agents.planning_agent import run

if __name__ == "__main__":
    result = run(
        "Plan the optimal route for the messenger to Skolwin. "
        "Start by discovering what tools and data sources are available."
    )
    print("\n=== Final Plan ===")
    print(result)
