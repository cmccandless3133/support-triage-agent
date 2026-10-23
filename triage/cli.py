"""Triage one ticket from the command line.

    python -m triage.cli --subject "Refund?" --body "I paid yesterday..." --plan Starter
"""
import argparse
import json

from .agent import make_agent
from .schema import Ticket


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--plan", default="Starter")
    p.add_argument("--agent", default="claude", choices=["claude", "baseline"])
    a = p.parse_args()
    result = make_agent(a.agent).triage(Ticket("CLI-1", a.subject, a.body, a.plan))
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
