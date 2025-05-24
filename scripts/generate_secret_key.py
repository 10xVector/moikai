import secrets
import base64

# Generate a secure random key
secret_key = secrets.token_hex(32)  # 32 bytes = 64 characters in hex
print("\nGenerated Secret Key:")
print(secret_key)

# Also generate a base64 encoded version (sometimes useful for certain services)
b64_key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
print("\nBase64 Encoded Key:")
print(b64_key)

print("\nInstructions:")
print("1. Copy one of these keys")
print("2. Add it to your .env file as: SECRET_KEY=your_copied_key")
print("3. For AWS, add it to Parameter Store using:")
print("   aws ssm put-parameter --name \"/moikai/secret-key\" --value \"your_copied_key\" --type SecureString") 