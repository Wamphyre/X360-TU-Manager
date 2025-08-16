import requests
import time
import os
from urllib.parse import quote

BASE_URL = "https://xboxunity.net/Api"
WEB_BASE_URL = "https://xboxunity.net"
RESOURCES_URL = "https://xboxunity.net/Resources/Lib"

def probar_conectividad():
    """Test basic connectivity with XboxUnity"""
    try:
        print("[INFO] Testing connectivity with XboxUnity...")
        r = requests.get("https://xboxunity.net", timeout=10)
        if r.status_code == 200:
            print("[INFO] Connectivity with XboxUnity: OK")
            return True
        else:
            print(f"[ERROR] XboxUnity responded with code: {r.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Cannot connect to XboxUnity: {e}")
        return False

def login_xboxunity(usuario, contrasena):
    """Login using username/password and return token"""
    url = f"{BASE_URL}/Auth/Login"
    headers = {
        "User-Agent": "UnityApp/1.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    datos = {
        "username": usuario,
        "password": contrasena
    }
    
    try:
        print(f"[INFO] Attempting to connect to XboxUnity: {url}")
        r = requests.post(url, data=datos, headers=headers, timeout=30)
        print(f"[INFO] Server response: {r.status_code}")
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"[INFO] JSON response received: {data}")
                if "token" in data:
                    print("[INFO] Token obtained successfully")
                    return data["token"]
                else:
                    print("[ERROR] Token not found in response")
            except Exception as e:
                print(f"[ERROR] Parsing login response: {e}")
                print(f"[ERROR] Response content: {r.text[:500]}")
        else:
            print(f"[ERROR] HTTP status code: {r.status_code}")
            print(f"[ERROR] Server response: {r.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout connecting to XboxUnity")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection error with XboxUnity")
    except Exception as e:
        print(f"[ERROR] Unexpected error in login: {e}")
    
    return None

def buscar_tus_con_endpoint_real(title_id, media_id=None, token=None, api_key=None):
    """
    Use the real XboxUnity endpoint found in page analysis
    Resources/Lib/TitleUpdateInfo.php - FILTERS BY SPECIFIC MEDIAID
    """
    print(f"[INFO] Using real TitleUpdateInfo endpoint for TitleID: {title_id}")
    if media_id:
        print(f"[INFO] Filtering TUs only for MediaID: {media_id}")
    
    try:
        # Real URL used by XboxUnity web
        url = f"{RESOURCES_URL}/TitleUpdateInfo.php"
        
        # Headers to simulate web AJAX request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://xboxunity.net/'
        }
        
        # Parameters used by real web
        params = {
            'titleid': title_id
        }
        
        print(f"[INFO] Querying: {url} with TitleID: {title_id}")
        r = requests.get(url, params=params, headers=headers, timeout=30)
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"[INFO] TitleUpdateInfo response received: {type(data)}")
                
                # Parse the real response structure
                if isinstance(data, dict):
                    tus_encontradas = []
                    
                    # Type 1: Response with MediaIDS (like ASURA'S WRATH)
                    if data.get('Type') == 1 and 'MediaIDS' in data:
                        print(f"[INFO] Response type 1 - with MediaIDS")
                        if media_id:
                            print(f"[INFO] Filtering TUs only for specific MediaID: {media_id}")
                        
                        for media_item in data['MediaIDS']:
                            item_media_id = media_item.get('MediaID', '')
                            updates = media_item.get('Updates', [])
                            
                            # If MediaID is specified, filter only that one
                            if media_id and item_media_id != media_id:
                                print(f"[INFO] Skipping MediaID {item_media_id} (doesn't match {media_id})")
                                continue
                            
                            print(f"[INFO] Processing MediaID: {item_media_id} ({len(updates)} updates)")
                            
                            for update in updates:
                                # Use original filename from API, fallback to generated name
                                original_name = update.get('Name', '')
                                if original_name and original_name.endswith('.tu'):
                                    file_name = original_name
                                else:
                                    file_name = f"{title_id}_{update.get('Version', '1')}.tu"
                                
                                tu_info = {
                                    'fileName': file_name,
                                    'downloadUrl': f"{RESOURCES_URL}/TitleUpdate.php?tuid={update.get('TitleUpdateID', '')}",
                                    'titleUpdateId': update.get('TitleUpdateID', ''),
                                    'version': update.get('Version', ''),
                                    'mediaId': item_media_id,
                                    'titleId': title_id,
                                    'titleName': original_name,
                                    'size': update.get('Size', 0),
                                    'uploadDate': update.get('UploadDate', ''),
                                    'hash': update.get('hash', ''),
                                    'baseVersion': update.get('BaseVersion', '')
                                }
                                
                                tus_encontradas.append(tu_info)
                                print(f"[INFO] TU found: {tu_info['fileName']} (MediaID: {tu_info['mediaId']}, Version: {tu_info['version']})")
                    
                    # Type 2: Response with direct Updates (like BAYONETTA)
                    elif data.get('Type') == 2 and 'Updates' in data:
                        print(f"[INFO] Response type 2 - with direct Updates")
                        updates = data.get('Updates', [])
                        
                        for update in updates:
                            update_media_id = update.get('MediaID', '')
                            
                            # If MediaID is specified, filter only that one
                            if media_id and update_media_id != media_id:
                                print(f"[INFO] Skipping TU with MediaID {update_media_id} (doesn't match {media_id})")
                                continue
                            
                            # Use original filename from API, fallback to generated name
                            original_name = update.get('Name', '')
                            if original_name and original_name.endswith('.tu'):
                                file_name = original_name
                            else:
                                file_name = f"{title_id}_{update.get('Version', '1')}.tu"
                            
                            tu_info = {
                                'fileName': file_name,
                                'downloadUrl': f"{RESOURCES_URL}/TitleUpdate.php?tuid={update.get('TitleUpdateID', '')}",
                                'titleUpdateId': update.get('TitleUpdateID', ''),
                                'version': update.get('Version', ''),
                                'mediaId': update_media_id,
                                'titleId': title_id,
                                'titleName': original_name,
                                'size': update.get('Size', 0),
                                'uploadDate': update.get('UploadDate', ''),
                                'hash': update.get('hash', ''),
                                'baseVersion': update.get('BaseVersion', '')
                            }
                            
                            tus_encontradas.append(tu_info)
                            print(f"[INFO] TU found: {tu_info['fileName']} (MediaID: {tu_info['mediaId']}, Version: {tu_info['version']})")
                    
                    # Other response types
                    else:
                        print(f"[INFO] Unrecognized response type: {data.get('Type', 'unknown')}")
                        print(f"[INFO] Complete structure: {data}")
                    
                    if len(tus_encontradas) > 0:
                        print(f"[INFO] Total TUs found with real endpoint: {len(tus_encontradas)}")
                        return tus_encontradas
                    else:
                        print(f"[INFO] No TUs available for TitleID {title_id} with MediaID {media_id}")
                        return []
                        
                elif isinstance(data, list) and len(data) == 0:
                    print(f"[INFO] No TUs available for TitleID {title_id}")
                    return []
                else:
                    print(f"[INFO] Unexpected response from real endpoint: {data}")
                    return []
                    
            except Exception as e:
                print(f"[ERROR] Error parsing TitleUpdateInfo response: {e}")
                print(f"[ERROR] Content: {r.text[:500]}")
                return []
        else:
            print(f"[ERROR] Error in TitleUpdateInfo: {r.status_code}")
            print(f"[ERROR] Response: {r.text[:200]}")
            return []
            
    except Exception as e:
        print(f"[ERROR] Error querying TitleUpdateInfo: {e}")
        return []

def buscar_tus(media_id=None, title_id=None, token=None, api_key=None):
    """
    Main function to search TUs - CLEAN VERSION
    Only uses the endpoint that actually works
    """
    print(f"[INFO] Starting TU search...")
    
    if media_id:
        print(f"[INFO] MediaID: {media_id}")
    if title_id:
        print(f"[INFO] TitleID: {title_id}")
    
    if not title_id:
        print("[ERROR] TitleID is required to search TUs")
        return []
    
    # Use the real TitleUpdateInfo.php endpoint (based on web analysis)
    print(f"[INFO] Testing real TitleUpdateInfo endpoint...")
    tus_reales = buscar_tus_con_endpoint_real(title_id, media_id=media_id, token=token, api_key=api_key)
    
    if tus_reales and len(tus_reales) > 0:
        return tus_reales
    else:
        print(f"[WARNING] No TUs found for TitleID: {title_id}")
        if media_id:
            print(f"[WARNING] With specific MediaID: {media_id}")
        return []

def descargar_tu(url, destino, progreso_callback=None):
    """Download a TU from the specified URL"""
    try:
        print(f"[INFO] Downloading from: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://xboxunity.net/'
        }
        
        # Create directory if it doesn't exist
        directorio = os.path.dirname(destino)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)
        
        r = requests.get(url, headers=headers, stream=True, timeout=60)
        
        if r.status_code == 200:
            total_size = int(r.headers.get('content-length', 0))
            print(f"[INFO] File size: {total_size} bytes")
            
            downloaded = 0
            with open(destino, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progreso_callback and total_size > 0:
                            progreso_callback(downloaded, total_size)
            
            print(f"[INFO] Download completed: {destino}")
            return True
        else:
            print(f"[ERROR] Download error: {r.status_code}")
            print(f"[ERROR] Response: {r.text[:200]}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error downloading TU: {e}")
        return False