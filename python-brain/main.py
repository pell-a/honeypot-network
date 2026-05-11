import os
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

app = FastAPI(title="AI Deception Brain")

class ThreatPayload(BaseModel):
    attacker_ip: str
    timestamp: str
    payload: str
    target_port: str

def block_ip_in_waf(ip_address: str):
    """
    Communicates with AWS WAFv2 via boto3 to append a malicious IP to a blocklist.
    """
    print(f"\n[*] AWS BOTO3: Initiating WAF update to block IP {ip_address}/32...")
    
    client = boto3.client('wafv2', region_name='us-east-1')
    
    try:
        ipset_name = 'DeceptionBlocklist'
        # PASTE YOUR TERRAFORM OUTPUT ID HERE
        ipset_id = 'aa250dc0-eef3-4aa6-b1bb-b55dd1e7649d' 
        
        print(f"[~] Fetching current WAF IPSet '{ipset_name}'...")
        response = client.get_ip_set(Name=ipset_name, Scope='REGIONAL', Id=ipset_id)
        
        # WAF requires a LockToken to prevent race conditions when updating
        lock_token = response['LockToken']
        addresses = response['IPSet']['Addresses']
        
        print(f"[~] Appending {ip_address}/32 to the blocklist...")
        # WAF requires standard CIDR notation, so a single IP must have /32 appended
        new_ip_cidr = f"{ip_address}/32"
        
        if new_ip_cidr not in addresses:
            addresses.append(new_ip_cidr)
            
            print(f"[~] Pushing updated blocklist to AWS WAF...")
            client.update_ip_set(
                Name=ipset_name, 
                Scope='REGIONAL', 
                Id=ipset_id, 
                Addresses=addresses, 
                LockToken=lock_token
            )
            print("[+] AWS BOTO3: SUCCESS. Attacker is now blocked globally at the cloud edge.")
        else:
            print("[-] IP is already in the blocklist. No update required.")
            
    except Exception as e:
        print(f"[!] AWS BOTO3 ERROR: Failed to update WAF - {e}")


@app.post("/analyze")
async def analyze_threat(threat: ThreatPayload):
    print(f"\n{'='*50}\n[*] ALERT: Received payload from {threat.attacker_ip} targeting port {threat.target_port}")
    print(f"[-] Raw Data: {threat.payload.strip()}")
    
    prompt = f"""
    You are an expert cloud security analyst analyzing telemetry from a honeypot.
    
    Attacker IP: {threat.attacker_ip}
    Target Port: {threat.target_port}
    Raw Payload: {threat.payload}
    
    Task: Analyze the raw payload. What is the attacker attempting to do? 
    Extract any specific file paths, URLs, or commands they are trying to execute.
    Keep the response to 2 short sentences.
    """
    
    try:
        if model:
            response = model.generate_content(prompt)
            analysis_result = response.text.strip()
        else:
            analysis_result = "MOCK AI: Attacker is attempting a classic Redis unauthorized access exploit to overwrite SSH keys."
            
        print(f"\n[+] AI Analysis:\n{analysis_result}")
        
        # --- NEW: Trigger the Automated Remediation ---
        # If the AI flags this as an attack, trigger the AWS WAF block
        block_ip_in_waf(threat.attacker_ip)
        
        return {
            "status": "success",
            "action_taken": "ip_blocked_in_waf",
            "malicious_ip": threat.attacker_ip,
            "ai_report": analysis_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))