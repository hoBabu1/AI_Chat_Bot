import json
import ollama
from llama_index.core import Document, VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
import os

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

def query_with_rag(json_data, question):
    """RAG method: Query using LlamaIndex with vector search"""
    try:
        print("🔧 Setting up RAG system...")
        
        # Configure LlamaIndex to use Ollama with longer timeouts
        Settings.llm = Ollama(
            model="mistral", 
            request_timeout=300.0,  # 5 minutes timeout
            temperature=0.1
        )
        Settings.embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            request_timeout=300.0  # 5 minutes timeout
        )
        
        # Convert JSON data to documents with better chunking
        print("📄 Converting JSON to searchable documents...")
        documents = []
        
        # Handle different JSON structures with smaller chunks
        if isinstance(json_data, list):
            # If JSON is a list of items - chunk smaller pieces
            for i, item in enumerate(json_data[:10]):  # Limit to first 10 items to avoid timeout
                # Make smaller chunks for better processing
                text_content = json.dumps(item, ensure_ascii=False)
                if len(text_content) > 1000:  # Split large items
                    text_content = text_content[:1000] + "..."
                doc = Document(text=text_content, metadata={"index": i, "type": "json_item"})
                documents.append(doc)
        elif isinstance(json_data, dict):
            # If JSON is a dictionary, create smaller documents
            for key, value in list(json_data.items())[:10]:  # Limit to first 10 keys
                text_content = f"Key: {key}\nContent: {json.dumps(value, ensure_ascii=False)}"
                if len(text_content) > 1000:  # Split large content
                    text_content = text_content[:1000] + "..."
                doc = Document(text=text_content, metadata={"key": key, "type": "json_field"})
                documents.append(doc)
        else:
            # If JSON is a single value
            text_content = json.dumps(json_data, ensure_ascii=False)
            if len(text_content) > 1000:
                text_content = text_content[:1000] + "..."
            doc = Document(text=text_content, metadata={"type": "json_data"})
            documents.append(doc)
        
        print(f"✓ Created {len(documents)} searchable documents")
        
        # Create vector index with progress indication
        print("🔍 Creating vector index (this may take 2-3 minutes)...")
        print("⏳ Please wait... (embedding documents)")
        
        try:
            index = VectorStoreIndex.from_documents(
                documents, 
                show_progress=True  # Show progress if available
            )
        except Exception as index_error:
            print(f"❌ Index creation failed: {index_error}")
            print("🔄 Trying with smaller batch...")
            # Try with even fewer documents
            smaller_docs = documents[:5]
            index = VectorStoreIndex.from_documents(smaller_docs)
        
        # Create query engine with optimized settings
        print("⚡ Setting up query engine...")
        query_engine = index.as_query_engine(
            similarity_top_k=2,  # Reduce to 2 most relevant chunks
            response_mode="compact",  # Compact response format
            streaming=False
        )
        
        # Query the engine with timeout handling
        print("🤖 Querying with RAG...")
        print("⏳ This may take 1-2 minutes...")
        
        import time
        start_time = time.time()
        
        response = query_engine.query(question)
        
        end_time = time.time()
        print(f"✅ Query completed in {end_time - start_time:.1f} seconds")
        
        return str(response)
        
    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ RAG Error: {e}")
        
        # Provide specific troubleshooting based on error type
        if "timeout" in error_msg or "timed out" in error_msg:
            print("\n🔧 TIMEOUT SOLUTIONS:")
            print("1. Try again - sometimes it works on retry")
            print("2. Check if Ollama is running: ollama list")
            print("3. Restart Ollama: ollama stop && ollama start")
            print("4. Try smaller data or use Original method for now")
        elif "connection" in error_msg:
            print("\n🔧 CONNECTION SOLUTIONS:")
            print("1. Make sure Ollama is running: ollama serve")
            print("2. Check if models are available: ollama list")
        else:
            print("💡 Make sure you have installed: pip install llama-index llama-index-llms-ollama llama-index-embeddings-ollama")
            print("💡 And pulled the embedding model: ollama pull nomic-embed-text")
            
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

def telegram_queries_with_rag():
    """Handle telegram channel queries using RAG"""
    # Load JSON file
    data = load_json_file("telegram_channel_data.json")
    if not data:
        return
    
    print("🔍 Telegram Data Analysis with RAG - Type 'exit' to return to main menu")
    print("ℹ️  RAG will find the most relevant parts of your data to answer questions")
    
    while True:
        question = input("\n❓ Your question about telegram data (RAG): ")
        
        if question.lower() == 'exit':
            break
        
        # Get response using RAG
        response = query_with_rag(data, question)
        
        if response:
            print(f"\n🤖 RAG Answer:\n{response}")
        else:
            print("❌ Failed to get RAG response")

def pdf_queries_with_rag():
    """Handle PDF queries using RAG"""
    print("📄 PDF Analysis with RAG - Type 'exit' to return to main menu")
    print("ℹ️  Place your PDF files in a 'pdfs' folder in the same directory")
    
    # Check if pdfs folder exists
    pdf_folder = "pdfs"
    if not os.path.exists(pdf_folder):
        print(f"❌ '{pdf_folder}' folder not found. Creating it now...")
        os.makedirs(pdf_folder)
        print(f"✅ Created '{pdf_folder}' folder. Please add your PDF files there and restart.")
        return
    
    # Check if there are PDF files
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"❌ No PDF files found in '{pdf_folder}' folder.")
        print("💡 Add some PDF files to the folder and try again.")
        return
    
    print(f"✅ Found {len(pdf_files)} PDF file(s): {', '.join(pdf_files)}")
    
    try:
        print("🔧 Setting up PDF RAG system...")
        
        # Configure LlamaIndex to use Ollama with extended timeouts
        Settings.llm = Ollama(
            model="mistral", 
            request_timeout=600.0,  # 10 minutes timeout
            temperature=0.1
        )
        Settings.embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            request_timeout=600.0  # 10 minutes timeout
        )
        
        # Load PDF documents
        print("📄 Loading and processing PDF files...")
        reader = SimpleDirectoryReader(input_dir=pdf_folder)
        documents = reader.load_data()
        
        # Limit documents if too many to avoid timeouts
        if len(documents) > 50:
            print(f"⚠️  Found {len(documents)} chunks. Using first 50 to avoid timeout.")
            documents = documents[:50]
        
        print(f"✓ Loaded {len(documents)} document chunks from PDFs")
        
        # Create vector index
        print("🔍 Creating vector index (this may take a moment)...")
        index = VectorStoreIndex.from_documents(documents)
        
        # Create query engine with optimized settings
        print("⚡ Setting up query engine...")
        query_engine = index.as_query_engine(
            similarity_top_k=3,  # Retrieve top 3 most relevant chunks
            response_mode="compact",  # Compact response format
            streaming=False
        )
        
        print("✅ PDF RAG system ready!")
        
        while True:
            question = input("\n❓ Your question about the PDF content: ")
            
            if question.lower() == 'exit':
                break
            
            try:
                print("🤖 Searching through PDFs...")
                print("⏳ Please wait (this may take 1-2 minutes)...")
                
                # Add timeout handling for queries
                import time
                start_time = time.time()
                
                # Try query with error handling
                try:
                    response = query_engine.query(question)
                    end_time = time.time()
                    print(f"✅ Query completed in {end_time - start_time:.1f} seconds")
                    print(f"\n🤖 PDF RAG Answer:\n{response}")
                    
                except Exception as query_error:
                    print(f"❌ Query timeout/error: {query_error}")
                    print("\n🔧 TRYING SIMPLER APPROACH...")
                    
                    # Fallback: Try with fewer chunks
                    simple_engine = index.as_query_engine(
                        similarity_top_k=1,  # Just 1 chunk
                        response_mode="refine"  # Different mode
                    )
                    
                    try:
                        print("🔄 Retrying with simpler settings...")
                        response = simple_engine.query(question)
                        print(f"\n🤖 PDF RAG Answer (Simple):\n{response}")
                    except:
                        print("❌ Both approaches failed. The PDF content might be too complex.")
                        print("💡 Try asking a more specific question or use shorter PDFs.")
                
            except Exception as e:
                print(f"❌ Query error: {e}")
                print("\n🔧 TROUBLESHOOTING TIPS:")
                print("1. Try a shorter, more specific question")
                print("2. Restart the program and try again")
                print("3. Use smaller PDF files")
                print("4. Check if Ollama is running properly: ollama list")
                
    except Exception as e:
        print(f"❌ PDF RAG Setup Error: {e}")
        print("💡 Make sure you have installed: pip install llama-index[pdf]")
        print("💡 And that your PDF files are readable")

def show_menu():
    """Display main menu options"""
    print("\n" + "="*50)
    print("🤖 OLLAMA CHAT ASSISTANT")
    print("="*50)
    print("1️⃣  Chat with GPT")
    print("2️⃣  Queries related to my telegram channel (Original)")
    print("3️⃣  Queries related to my telegram channel (RAG)")
    print("4️⃣  Queries related to PDF documents (RAG)")
    print("5️⃣  Exit")
    print("-"*50)
    print("💡 RAG = Retrieval-Augmented Generation (Smarter search)")

def main():
    while True:
        show_menu()
        choice = input("🎯 Select an option (1/2/3/4/5): ").strip()
        
        if choice == '1':
            chat_with_gpt()
        elif choice == '2':
            telegram_queries()
        elif choice == '3':
            telegram_queries_with_rag()
        elif choice == '4':
            pdf_queries_with_rag()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()