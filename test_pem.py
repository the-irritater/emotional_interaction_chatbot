import re

def fix_pem(raw_key):
    # Try replacing literal \n if present
    key = raw_key.replace("\\n", "\n")
    
    # Extract just the base64 part
    header = "-BEGIN PRIVATE KEY-"
    footer = "-END PRIVATE KEY-"
    
    if header in key and footer in key:
        b64 = key.split(header)[1].split(footer)[0]
        # Remove all whitespace
        b64 = re.sub(r'\s+', '', b64)
        
        # Add proper padding if missing
        pad_len = len(b64) % 4
        if pad_len:
            b64 += "=" * (4 - pad_len)
            
        # Re-chunk into 64 character lines
        chunks = [b64[i:i+64] for i in range(0, len(b64), 64)]
        
        return f"{header}\n" + "\n".join(chunks) + f"\n{footer}\n"
    return key

