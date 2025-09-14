import json
import ollama

def load_json_file(file_path):
    """Load JSON file"""
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Loaded {file_path}")
        return data
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None

def chat_with_gpt():
    """Chat with Mistral model like ChatGPT"""
    print("🤖 Chat Mode - Type 'exit' to return to main menu")
    
    while True:
        question = input("\n💬 Your question: ")
        
        if question.lower() == 'exit':
            break
            
        try:
            print("🤖 Thinking...")
            
            response = ollama.chat(
                model="mistral",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Provide clear, informative responses."},
                    {"role": "user", "content": question}
                ],
                stream=False
            )
            
            print(f"\n🤖 Response:\n{response['message']['content']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def query_mistral(json_data, question):
    """Query Mistral with entire JSON data"""
    try:
        # Convert JSON to string
        json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # Create the prompt
        prompt = f"""Here is the JSON data:

{json_string}

Question: {question}

Please answer based on the provided data."""

        print("🤖 Querying Mistral...")
        
        # Query Ollama
        response = ollama.chat(
            model="mistral",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer questions based on the provided JSON data."},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        return response["message"]["content"]
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def telegram_queries():
    """Handle telegram channel queries"""
    # Load JSON file
    data = load_json_file("telegram_channel_data.json")
    if not data:
        return
    
    print("📊 Telegram Data Analysis Mode - Type 'exit' to return to main menu")
    
    while True:
        question = input("\n❓ Your question about telegram data: ")
        
        if question.lower() == 'exit':
            break
        
        # Get response
        response = query_mistral(data, question)
        
        if response:
            print(f"\n🤖 Answer:\n{response}")
        else:
            print("❌ Failed to get response")

def show_menu():
    """Display main menu options"""
    print("\n" + "="*50)
    print("🤖 OLLAMA CHAT ASSISTANT")
    print("="*50)
    print("1️⃣  Chat with GPT")
    print("2️⃣  Queries related to my telegram channel")
    print("3️⃣  Exit")
    print("-"*50)

def main():
    while True:
        show_menu()
        choice = input("🎯 Select an option (1/2/3): ").strip()
        
        if choice == '1':
            chat_with_gpt()
        elif choice == '2':
            telegram_queries()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()