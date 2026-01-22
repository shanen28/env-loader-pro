"""Encrypted configuration lifecycle management."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from ..exceptions import DecryptionError


def encrypt_file(
    input_path: str,
    output_path: Optional[str] = None,
    method: str = "age",
    key_path: Optional[str] = None,
) -> None:
    """Encrypt a .env file.
    
    Args:
        input_path: Path to input file
        output_path: Path to output file (default: input_path + .enc)
        method: Encryption method (age, gpg)
        key_path: Path to encryption key
    
    Raises:
        DecryptionError: If encryption fails
    """
    if output_path is None:
        output_path = f"{input_path}.enc"
    
    if method == "age":
        _encrypt_with_age(input_path, output_path, key_path)
    elif method == "gpg":
        _encrypt_with_gpg(input_path, output_path, key_path)
    else:
        raise DecryptionError(f"Unsupported encryption method: {method}")


def decrypt_file(
    input_path: str,
    output_path: Optional[str] = None,
    key_path: Optional[str] = None,
) -> None:
    """Decrypt an encrypted .env file.
    
    Args:
        input_path: Path to encrypted file
        output_path: Path to output file (default: input_path without .enc)
        key_path: Path to decryption key
    
    Raises:
        DecryptionError: If decryption fails
    """
    if output_path is None:
        if input_path.endswith(".enc"):
            output_path = input_path[:-4]
        else:
            output_path = f"{input_path}.decrypted"
    
    # Use decryptor registry
    from .decryptor import get_decryptor_registry
    
    registry = get_decryptor_registry()
    decrypted_content = registry.decrypt(input_path, key_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(decrypted_content)


def _encrypt_with_age(
    input_path: str,
    output_path: str,
    key_path: Optional[str] = None,
) -> None:
    """Encrypt file with age."""
    try:
        cmd = ["age", "--encrypt"]
        
        if key_path:
            cmd.extend(["-i", key_path])
        
        cmd.append("-o")
        cmd.append(output_path)
        
        with open(input_path, "rb") as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                check=True,
            )
    except FileNotFoundError:
        raise DecryptionError(
            "age tool not found. Install age: https://github.com/FiloSottile/age"
        )
    except subprocess.CalledProcessError as e:
        raise DecryptionError(f"age encryption failed: {e.stderr.decode() if e.stderr else str(e)}")


def _encrypt_with_gpg(
    input_path: str,
    output_path: str,
    key_path: Optional[str] = None,
) -> None:
    """Encrypt file with GPG."""
    try:
        cmd = ["gpg", "--encrypt", "--output", output_path]
        
        if key_path:
            # GPG recipient key
            cmd.extend(["--recipient", key_path])
        
        cmd.append(input_path)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        raise DecryptionError(
            "GPG not found. Install GPG: https://www.gnupg.org/"
        )
    except subprocess.CalledProcessError as e:
        raise DecryptionError(f"GPG encryption failed: {e.stderr.decode() if e.stderr else str(e)}")


def re_encrypt_file(
    encrypted_path: str,
    output_path: Optional[str] = None,
    key_path: Optional[str] = None,
    new_method: Optional[str] = None,
) -> None:
    """Decrypt and re-encrypt a file (never store plaintext on disk).
    
    Args:
        encrypted_path: Path to encrypted file
        output_path: Path to output file
        key_path: Decryption key path
        new_method: New encryption method (if different)
    
    Raises:
        DecryptionError: If operation fails
    """
    # Decrypt to memory
    from .decryptor import get_decryptor_registry
    
    registry = get_decryptor_registry()
    decrypted_content = registry.decrypt(encrypted_path, key_path)
    
    # Determine method from output path or use same
    if output_path is None:
        output_path = encrypted_path
    
    method = new_method or ("age" if encrypted_path.endswith(".age") else "gpg")
    
    # Re-encrypt
    # Write to temp file first, then encrypt
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".tmp") as tmp:
        tmp.write(decrypted_content)
        tmp_path = tmp.name
    
    try:
        encrypt_file(tmp_path, output_path, method=method, key_path=key_path)
    finally:
        # Clean up temp file
        os.unlink(tmp_path)
