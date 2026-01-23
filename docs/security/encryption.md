# Encrypted Files

Support for encrypted .env files using age, GPG, or OpenSSL.

## Supported Methods

- **age** - Modern encryption tool (recommended)
- **GPG** - GNU Privacy Guard
- **openssl** - OpenSSL encryption

## Encrypting Files

### CLI

```bash
# Encrypt with age (default)
envloader encrypt .env

# Encrypt with specific method
envloader encrypt .env --method gpg
envloader encrypt .env --method openssl

# Specify output file
envloader encrypt .env --output .env.enc

# Specify key
envloader encrypt .env --key /path/to/key
```

### Python API

```python
from env_loader_pro.crypto import encrypt_file

encrypt_file(
    input_path=".env",
    output_path=".env.enc",
    method="age",
    key="/path/to/key"
)
```

## Decrypting Files

### CLI

```bash
# Decrypt
envloader decrypt .env.enc

# Specify output
envloader decrypt .env.enc --output .env

# Specify key
envloader decrypt .env.enc --key /path/to/key
```

### Python API

```python
from env_loader_pro.crypto import decrypt_file

decrypted_content = decrypt_file(
    input_path=".env.enc",
    output_path=".env",
    method="age",
    key="/path/to/key"
)
```

## Loading Encrypted Files

### Direct Load

```python
from env_loader_pro import load_env

config = load_env(
    path=".env.enc",
    encrypted=True,
    encryption_key="/path/to/key"
)
```

### Auto-Detection

```python
# Automatically detects .env.enc
config = load_env(path=".env.enc")
```

## Re-Encryption

Change encryption method or key:

```python
from env_loader_pro.crypto import re_encrypt_file

re_encrypt_file(
    input_path=".env.enc",
    output_path=".env.enc.new",
    old_method="age",
    new_method="gpg",
    old_key="/path/to/old/key",
    new_key="/path/to/new/key"
)
```

**Guarantee**: Plaintext is never persisted to disk during re-encryption.

## Best Practices

1. **Use age** for modern encryption
2. **Store keys securely** (not in repo)
3. **Rotate keys** regularly
4. **Use different keys** per environment
5. **Never commit encrypted files** with keys

## Related Topics

- [Security Model](../security/model.md)
- [CI/CD Safety](../security/ci-safety.md)
