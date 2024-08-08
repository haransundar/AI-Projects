from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

# Create a new chatbot instance
chatbot = ChatBot('BasicBot')

# Create a new trainer for the chatbot
trainer = ChatterBotCorpusTrainer(chatbot)

# Train the chatbot using the English corpus data
trainer.train("chatterbot.corpus.english")

# Function to get response from the chatbot
def get_response(question):
    return chatbot.get_response(question)

# Example usage
while True:
    user_input = input("You: ")
    response = get_response(user_input)
    print("Bot:", response)
