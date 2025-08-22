from agents.agent import create_agent 
agent = create_agent()

response = agent.ask_simple_question("MISA cam kết 2500 tỷ làm gì?")
print(response)