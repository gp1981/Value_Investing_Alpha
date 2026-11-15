import os
import logging
import getpass

try:
    import keyring
except ImportError:
    keyring = None

logger = logging.getLogger(__name__)

def get_credentials(base_service_name):
    """
    Retrieves username and password stored as separate Keychain items.
    Example: 'MF_username' and 'MF_password'
    """
    # Normalize the base name to strip trailing underscore
    base = base_service_name.rstrip('_')
    
    # 1. Define the keys for Environment Variables
    user_env_key = f"{base.upper()}_USER"
    pass_env_key = f"{base.upper()}_PASS"

    # 2. Try Environment Variables
    user = os.getenv(user_env_key)
    password = os.getenv(pass_env_key)

    if user and password:
        return user, password

    # 3. Fallback to Keychain
    if keyring:
        # Use MF_username and MF_password
        keychain_user_service = f"{base}_username"
        keychain_pass_service = f"{base}_password"
        
        # Retrieve without account name, as these items are stored as application passwords
        retrieved_user = keyring.get_password(keychain_user_service, None)
        retrieved_pass = keyring.get_password(keychain_pass_service, None)

        if retrieved_user and retrieved_pass:
            return retrieved_user, retrieved_pass

    logger.error(f"Could not find entries for {base} (Looked for services: {keychain_user_service}, {keychain_pass_service})")
    return None, None