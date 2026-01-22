"""GPG encryption/decryption support."""

import subprocess
from typing import Optional

from ..exceptions import DecryptionError
from .decryptor import Decryptor


class GPGDecryptor(Decryptor):
    """Decryptor for GPG-encrypted files."""
    
    def decrypt(self, encrypted_path: str, key: Optional[str] = None) -> str:
        """Decrypt a GPG-encrypted file.
        
        Args:
            encrypted_path: Path to encrypted file
            key: Optional passphrase (not recommended, use GPG agent instead)
        
        Returns:
            Decrypted content
        
        Raises:
            DecryptionError: If decryption fails
        """
        try:
            cmd = ["gpg", "--decrypt", "--quiet", "--yes"]
            
            if key:
                # Note: Using passphrase via command line is insecure
                # Better to use GPG agent or keyring
                cmd.extend(["--passphrase", key, "--batch"])
            
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
                "GPG not found. Install GPG: https://www.gnupg.org/"
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e.stdout or str(e)
            raise DecryptionError(
                f"GPG decryption failed: {error_msg}"
            )
        except Exception as e:
            raise DecryptionError(f"Unexpected error during GPG decryption: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if GPG is available.
        
        Returns:
            True if gpg command is available
        """
        try:
            result = subprocess.run(
                ["gpg", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
        except Exception:
            return False
