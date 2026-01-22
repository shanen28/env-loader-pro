"""age encryption/decryption support."""

import subprocess
from typing import Optional

from ..exceptions import DecryptionError
from .decryptor import Decryptor


class AgeDecryptor(Decryptor):
    """Decryptor for age-encrypted files."""
    
    def decrypt(self, encrypted_path: str, key: Optional[str] = None) -> str:
        """Decrypt an age-encrypted file.
        
        Args:
            encrypted_path: Path to encrypted file
            key: Optional path to age identity file
        
        Returns:
            Decrypted content
        
        Raises:
            DecryptionError: If decryption fails
        """
        try:
            cmd = ["age", "--decrypt"]
            
            if key:
                cmd.extend(["-i", key])
            
            cmd.append(encrypted_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout
        except FileNotFoundError:
            raise DecryptionError(
                "age tool not found. Install age: https://github.com/FiloSottile/age"
            )
        except subprocess.CalledProcessError as e:
            raise DecryptionError(
                f"age decryption failed: {e.stderr or str(e)}"
            )
        except Exception as e:
            raise DecryptionError(f"Unexpected error during age decryption: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if age is available.
        
        Returns:
            True if age command is available
        """
        try:
            result = subprocess.run(
                ["age", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
        except Exception:
            return False
