"""
Secure API Key Loader
Loads Gemini API key from secure sources, never from project files
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def load_gemini_api_key() -> Optional[str]:
    """
    Load Gemini API key from secure sources in order of preference:
    1. Environment variable (most secure)
    2. Secure file outside project
    3. Windows Credential Manager
    
    Returns:
        API key string or None if not found
    """
    
    # Method 1: Environment variable (set with setx or in system)
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        logger.info("✅ Gemini API key loaded from environment variable")
        return api_key.strip()
    
    # Method 2: Secure file outside project
    secure_paths = [
        r'C:\secure-keys\.env',
        Path.home() / '.gemini' / '.env',
        Path.home() / '.secure' / '.env'
    ]
    
    for path in secure_paths:
        if Path(path).exists():
            try:
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('GEMINI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            logger.info(f"✅ Gemini API key loaded from secure file: {path}")
                            return api_key
            except Exception as e:
                logger.warning(f"Failed to read secure file {path}: {e}")
    
    # Method 3: Windows Credential Manager (if available)
    try:
        import keyring
        api_key = keyring.get_password("gemini-api", "icu-assistant")
        if api_key:
            logger.info("✅ Gemini API key loaded from Windows Credential Manager")
            return api_key
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to load from credential manager: {e}")
    
    logger.error("❌ No Gemini API key found in any secure location")
    return None


def store_gemini_api_key_securely(api_key: str, method: str = "file") -> bool:
    """
    Store API key securely outside the project.
    
    Args:
        api_key: The API key to store
        method: Storage method ("file", "env", or "credential")
    
    Returns:
        True if successful, False otherwise
    """
    
    if method == "file":
        secure_file = Path(r'C:\secure-keys\.env')
        secure_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(secure_file, 'w') as f:
                f.write(f"GEMINI_API_KEY={api_key}\n")
            logger.info(f"✅ API key stored securely in: {secure_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store API key in file: {e}")
            return False
    
    elif method == "credential":
        try:
            import keyring
            keyring.set_password("gemini-api", "icu-assistant", api_key)
            logger.info("✅ API key stored in Windows Credential Manager")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store in credential manager: {e}")
            return False
    
    return False


def test_gemini_connection() -> bool:
    """
    Test if Gemini API key works without exposing it.
    
    Returns:
        True if connection successful, False otherwise
    """
    api_key = load_gemini_api_key()
    if not api_key:
        logger.error("❌ No API key available for testing")
        return False
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Test with minimal request using available model
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content("Hello")
        
        if response and response.text:
            logger.info("✅ Gemini API connection successful")
            return True
        else:
            logger.error("❌ Gemini API returned empty response")
            return False
            
    except Exception as e:
        logger.error(f"❌ Gemini API test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the secure loader
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing secure API key loader...")
    
    key = load_gemini_api_key()
    if key:
        print(f"✅ Found API key (length: {len(key)})")
        
        # Test connection
        if test_gemini_connection():
            print("✅ API key works correctly")
        else:
            print("❌ API key test failed")
    else:
        print("❌ No API key found")
        print("\nTo add a key securely:")
        print("1. Set environment variable: setx GEMINI_API_KEY your_key_here")
        print("2. Or create file: C:\\secure-keys\\.env")