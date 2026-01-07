from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from agents_test.run_agents_test import run_agents_test
from single_agent_test.run_single_agent_test import run_single_agent_test


def main():
    run_agents_test()
    run_single_agent_test()
    print("✓ Agent tests complete. See agents_test/ and single_agent_test/")


if __name__ == "__main__":
    main()
