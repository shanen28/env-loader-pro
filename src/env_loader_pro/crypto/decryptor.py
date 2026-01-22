"""Generic decryption interface for encrypted .env files."""

from abc import ABC, abstractmethod
from typing import Optional

from ..exceptions import DecryptionError


class Decryptor(ABC):
    """Abstract base class for decryptors."""
    
    @abstractmethod
    def decrypt(self, encrypted_path: str, key: Optional[str] = None) -> str:
        """Decrypt a file.
        
        Args:
            encrypted_path: Path to encrypted file
            key: Optional decryption key or path to key file
        
        Returns:
            Decrypted content as string
        
        Raises:
            DecryptionError: If decryption fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if decryption tool is available.
        
        Returns:
            True if decryption tool is installed and available
        """
        pass


class DecryptorRegistry:
    """Registry for decryptors."""
    
    def __init__(self):
        """Initialize registry."""
        self._decryptors: list[Decryptor] = []
    
    def register(self, decryptor: Decryptor) -> None:
        """Register a decryptor.
        
        Args:
            decryptor: Decryptor instance
        """
        self._decryptors.append(decryptor)
    
    def decrypt(self, encrypted_path: str, key: Optional[str] = None) -> str:
        """Try to decrypt using registered decryptors.
        
        Args:
            encrypted_path: Path to encrypted file
            key: Optional decryption key
        
        Returns:
            Decrypted content
        
        Raises:
            DecryptionError: If all decryptors fail
        """
        errors = []
        
        for decryptor in self._decryptors:
            if not decryptor.is_available():
                continue
            
            try:
                return decryptor.decrypt(encrypted_path, key)
            except DecryptionError as e:
                errors.append(f"{decryptor.__class__.__name__}: {str(e)}")
            except Exception as e:
                errors.append(f"{decryptor.__class__.__name__}: Unexpected error: {str(e)}")
        
        raise DecryptionError(
            f"Failed to decrypt {encrypted_path}. Tried {len(self._decryptors)} decryptors. "
            f"Errors: {', '.join(errors)}"
        )


# Global registry instance
_default_registry: Optional[DecryptorRegistry] = None


def get_decryptor_registry() -> DecryptorRegistry:
    """Get or create default decryptor registry.
    
    Returns:
        DecryptorRegistry instance with default decryptors registered
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = DecryptorRegistry()
        
        # Register default decryptors
        try:
            from .age import AgeDecryptor
            _default_registry.register(AgeDecryptor())
        except ImportError:
            pass
        
        try:
            from .gpg import GPGDecryptor
            _default_registry.register(GPGDecryptor())
        except ImportError:
            pass
    
    return _default_registry
