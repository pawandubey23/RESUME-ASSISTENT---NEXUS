import os

# DON'T use dotenv - read directly
print("="*50)
print("DIRECT .env FILE CHECK")
print("="*50)

# Read .env file manually
try:
    with open('.env', 'r') as f:
        content = f.read()
        print("✅ .env file contents:")
        print(content)
        print("="*50)
except FileNotFoundError:
    print("❌ .env file not found!")

# Now test with dotenv
from dotenv import load_dotenv
load_dotenv(override=True)  # Force override

api_key = os.getenv("OPENAI_API_KEY")

print("\nAPI KEY INFO:")
if api_key:
    print(f"✅ Key loaded: {api_key[:20]}...")
    print(f"   Total length: {len(api_key)}")
    print(f"   Last 10 chars: ...{api_key[-10:]}")
else:
    print("❌ No key loaded")

print("="*50)

# Test OpenAI
if api_key and len(api_key) > 30:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        print("\n🧪 Testing OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'success'"}],
            max_tokens=5
        )
        print("✅ SUCCESS! OpenAI works!")
        print(f"   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
else:
    print("⚠️ Key too short or missing - not testing API")
