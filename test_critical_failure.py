import os

def database_connect():
    # ❌ HARDCODED SECRET (Trigger for Beast Mode)
    api_key = "sk-1234567890abcdef1234567890abcdef" 
    print(f"Connecting with {api_key}")

def dangerous_cleanup():
    # ❌ DANGEROUS EXECUTION
    user_input = "rm -rf /"
    os.system(user_input)

if __name__ == "__main__":
    database_connect()
