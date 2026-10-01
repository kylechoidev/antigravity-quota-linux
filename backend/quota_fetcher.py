"""Quota fetching engine for Antigravity accounts."""
import datetime
import json
import re
import subprocess
import time
import urllib3
import uuid
import requests

from auth_manager import refresh_access_token, load_accounts
from config import CLOUD_CODE_ENDPOINT, PROD_CLOUD_CODE_ENDPOINT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_time_delta(iso_reset_time):
    if not iso_reset_time:
        return "N/A"
    try:
        iso_str = iso_reset_time.replace("Z", "+00:00")
        target_time = datetime.datetime.fromisoformat(iso_str)
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = target_time - now
        total_seconds = int(diff.total_seconds())

        if total_seconds <= 0:
            return "Ready"

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 and days == 0:
            parts.append(f"{minutes}m")
        if not parts:
            parts.append(f"{seconds}s")
        return "in " + " ".join(parts)
    except Exception:
        return iso_reset_time

def find_active_language_server():
    try:
        ps_out = subprocess.check_output(["ps", "-eo", "pid,args"], text=True)
        csrf_token = None
        server_pid = None

        for line in ps_out.splitlines():
            if "language_server" in line and "--csrf_token" in line:
                m = re.search(r"--csrf_token[=\s]+([a-zA-Z0-9_\-]+)", line)
                if m:
                    csrf_token = m.group(1)
                    server_pid = line.strip().split()[0]
                    break

        if not csrf_token or not server_pid:
            return None, None

        ports = []
        try:
            ss_out = subprocess.check_output(["ss", "-tulpn"], text=True, stderr=subprocess.DEVNULL)
            for s_line in ss_out.splitlines():
                if f"pid={server_pid}," in s_line:
                    port_match = re.search(r"127\.0\.0\.1:(\d+)", s_line)
                    if port_match:
                        ports.append(int(port_match.group(1)))
        except Exception:
            pass

        for port in ports:
            try:
                resp = requests.post(
                    f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus",
                    headers={
                        "Content-Type": "application/json",
                        "x-codeium-csrf-token": csrf_token,
                    },
                    json={},
                    verify=False,
                    timeout=1.5,
                )
                if resp.status_code == 200:
                    return port, csrf_token
            except Exception:
                continue

        return None, None
    except Exception:
        return None, None

def extract_quota_summary_data(summary_json, user_status_json=None):
    result = {
        "gemini": {
            "5h_remaining": 100.0,
            "5h_reset": "Ready",
            "weekly_remaining": 100.0,
            "weekly_reset": "Ready",
            "weekly_anchored": False,
            "weekly_desc": "",
        },
        "claude_gpt": {
            "5h_remaining": 100.0,
            "5h_reset": "Ready",
            "weekly_remaining": 100.0,
            "weekly_reset": "Ready",
            "weekly_anchored": False,
            "weekly_desc": "",
        },
        "plan": "Google AI Pro",
    }

    if user_status_json:
        user_tier = user_status_json.get("userTier", {})
        result["plan"] = user_tier.get("name") or user_tier.get("id") or "Active Plan"

    groups = summary_json.get("response", {}).get("groups", [])
    if not groups and "groups" in summary_json:
        groups = summary_json.get("groups", [])

    for group in groups:
        d_name = group.get("displayName", "").lower()
        target = None
        if "gemini" in d_name:
            target = result["gemini"]
        elif "claude" in d_name or "gpt" in d_name or "3p" in d_name:
            target = result["claude_gpt"]

        if not target:
            continue

        for bucket in group.get("buckets", []):
            window = bucket.get("window", "")
            fraction = bucket.get("remainingFraction", 1.0)
            pct = round(fraction * 100, 1)
            reset_str = parse_time_delta(bucket.get("resetTime"))
            desc = bucket.get("description") or ""

            if window == "5h":
                target["5h_remaining"] = pct
                target["5h_reset"] = reset_str
            elif window == "weekly":
                target["weekly_remaining"] = pct
                target["weekly_reset"] = reset_str
                # Anchored when consumption description exists or remaining fraction is below 0.99999
                target["weekly_anchored"] = bool(desc) or fraction < 0.99999
                target["weekly_desc"] = desc

    return result

def fetch_local_active_quota():
    port, csrf_token = find_active_language_server()
    if not port or not csrf_token:
        return {
            "status": "offline",
            "error": "Antigravity 2.0 language server not running.",
        }

    headers = {
        "Content-Type": "application/json",
        "x-codeium-csrf-token": csrf_token,
    }

    try:
        q_resp = requests.post(
            f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary",
            headers=headers,
            json={},
            verify=False,
            timeout=5,
        )
        if q_resp.status_code != 200:
            return {"status": "error", "error": f"Language server HTTP {q_resp.status_code}"}

        q_json = q_resp.json()

        u_resp = requests.post(
            f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus",
            headers=headers,
            json={},
            verify=False,
            timeout=5,
        )
        u_json = u_resp.json() if u_resp.status_code == 200 else {}

        parsed = extract_quota_summary_data(q_json, u_json)
        parsed["status"] = "online"
        parsed["last_updated"] = int(time.time())
        return parsed
    except Exception as e:
        return {"status": "error", "error": str(e)}

def fetch_oauth_account_quota(account):
    refresh_token = account.get("refresh_token")
    if not refresh_token:
        return {"status": "error", "error": "No refresh token."}

    try:
        access_token, _ = refresh_access_token(refresh_token)
    except Exception as e:
        return {"status": "error", "error": f"Token refresh failed: {e}"}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "antigravity/2.12.2 (Linux x86_64)",
    }

    endpoints = [CLOUD_CODE_ENDPOINT, PROD_CLOUD_CODE_ENDPOINT]
    last_err = None

    for ep in endpoints:
        url = f"{ep}/v1internal:retrieveUserQuotaSummary"
        try:
            resp = requests.post(url, headers=headers, json={}, timeout=8)
            if resp.status_code == 200:
                parsed = extract_quota_summary_data(resp.json())
                parsed["status"] = "online"
                parsed["last_updated"] = int(time.time())
                return parsed
            else:
                last_err = f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            last_err = str(e)

    return {"status": "error", "error": last_err or "Failed to query quota"}

def fetch_all_accounts_quota():
    accounts = load_accounts()
    if not accounts:
        return []

    results = []
    for acc in accounts:
        acc_type = acc.get("type", "oauth")
        name = acc.get("name", "Account")
        email = acc.get("email", "")

        if acc_type == "local_active":
            data = fetch_local_active_quota()
        else:
            data = fetch_oauth_account_quota(acc)

        data["name"] = name
        data["email"] = email
        data["type"] = acc_type
        results.append(data)

    return results

def kickstart_pool(access_token, pool="gemini"):
    """Fires a micro-ping to start the 7-day countdown on a specific quota pool."""
    if pool == "claude_gpt" or pool == "claude":
        model = "claude-sonnet-4-6"
        pool_key = "claude_gpt"
    else:
        model = "gemini-3.8-flash-high"
        pool_key = "gemini"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "antigravity/2.12.2 (Linux x86_64)",
    }

    body = {
        "project": "aicode-consumers",
        "model": model,
        "requestId": str(uuid.uuid4()),
        "request": {
            "contents": [
                {"role": "user", "parts": [{"text": "Reply with 1 word: Pong"}]}
            ]
        }
    }

    endpoints = [CLOUD_CODE_ENDPOINT, PROD_CLOUD_CODE_ENDPOINT]
    last_err = None
    for ep in endpoints:
        url = f"{ep}/v1internal:generateContent"
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                reply = ""
                try:
                    candidates = data.get("response", {}).get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            reply = parts[0].get("text", "").strip()
                except Exception:
                    pass
                return {
                    "status": "ok",
                    "pool": pool_key,
                    "model": model,
                    "reply": reply or "Pong",
                }
            else:
                last_err = f"HTTP {resp.status_code}: {resp.text[:120]}"
        except Exception as e:
            last_err = str(e)

    return {"status": "error", "pool": pool_key, "model": model, "error": last_err or "Unknown error"}

def kickstart_account(account, pools=None):
    """Refreshes tokens and triggers micro-pings for the specified pools on an account."""
    if pools is None:
        pools = ["gemini", "claude_gpt"]
    elif isinstance(pools, str):
        pools = [pools]

    # Normalize pool names
    normalized_pools = []
    for p in pools:
        p_lower = p.lower()
        if "claude" in p_lower or "gpt" in p_lower or "3p" in p_lower:
            normalized_pools.append("claude_gpt")
        else:
            normalized_pools.append("gemini")
    normalized_pools = list(dict.fromkeys(normalized_pools))

    refresh_token = account.get("refresh_token")
    if not refresh_token:
        return {
            "status": "error",
            "name": account.get("name"),
            "email": account.get("email"),
            "error": "Account does not have a stored OAuth refresh token (e.g. local session)."
        }

    try:
        access_token, _ = refresh_access_token(refresh_token)
    except Exception as e:
        return {
            "status": "error",
            "name": account.get("name"),
            "email": account.get("email"),
            "error": f"Token refresh failed: {e}"
        }

    results = {}
    for pool in normalized_pools:
        res = kickstart_pool(access_token, pool=pool)
        results[pool] = res

    # Brief delay for Google's quota accounting to reflect
    time.sleep(1.0)
    updated_quota = fetch_oauth_account_quota(account)
    updated_quota["name"] = account.get("name", "Account")
    updated_quota["email"] = account.get("email", "")
    updated_quota["type"] = account.get("type", "oauth")

    return {
        "status": "ok",
        "name": account.get("name"),
        "email": account.get("email"),
        "results": results,
        "quota": updated_quota,
    }

def kickstart_all_idle_accounts(pools=None, only_unanchored=True):
    """Kickstarts all registered OAuth accounts that have unanchored weekly limits."""
    accounts = load_accounts()
    if not accounts:
        return []

    summary = []
    for acc in accounts:
        if acc.get("type") == "local_active" or not acc.get("refresh_token"):
            continue

        target_pools = pools
        if only_unanchored:
            # Check current quota to see which pools are unanchored
            current_q = fetch_oauth_account_quota(acc)
            needed_pools = []
            if not current_q.get("gemini", {}).get("weekly_anchored", False):
                needed_pools.append("gemini")
            if not current_q.get("claude_gpt", {}).get("weekly_anchored", False):
                needed_pools.append("claude_gpt")

            if not needed_pools:
                # Already all anchored
                summary.append({
                    "status": "skipped",
                    "name": acc.get("name"),
                    "email": acc.get("email"),
                    "reason": "All requested pools already anchored",
                    "quota": current_q,
                })
                continue
            target_pools = needed_pools

        res = kickstart_account(acc, pools=target_pools)
        summary.append(res)

    return summary

