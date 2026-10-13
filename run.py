from llm_miner import LLMMiner
from llm_miner import JournalReader

# Load agent and parse XML/HTML file
agent = LLMMiner.from_config(config)
jr = JournalReader.from_file(/data/paper.xml, publisher)

# Run the agent on the parsed file
agent.run(jr)