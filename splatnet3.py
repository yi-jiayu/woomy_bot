import base64
import hashlib
import secrets
import urllib.parse
from typing import Literal, TypedDict

import httpx

NSOAPP_VERSION = "2.2.0"
APP_USER_AGENT = "woomy_bot/2.0.0"
SPLATNET3_VERSION = "1.0.0-d3a90678"
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
)


def _sha256(s: str):
    """Returns a URL-safe base64-encoded SHA256 hash of the given string without padding."""
    return (
        base64.urlsafe_b64encode(hashlib.sha256(s.encode()).digest())
        .decode()
        .rstrip("=")
    )


def request_session_token(client):
    state = secrets.token_urlsafe(32)
    session_token_code_verifier = secrets.token_urlsafe(32)
    session_token_code_challenge = _sha256(session_token_code_verifier)

    headers = {
        "User-Agent": BROWSER_USER_AGENT,
    }

    params = {
        "state": state,
        "redirect_uri": "npf71b963c1b7b6d119://auth",
        "client_id": "71b963c1b7b6d119",
        "scope": "openid user user.birthday user.mii user.screenName",
        "response_type": "session_token_code",
        "session_token_code_challenge": session_token_code_challenge,
        "session_token_code_challenge_method": "S256",
        "theme": "login_form",
    }
    print(params)

    response = client.get(
        url="https://accounts.nintendo.com/connect/1.0.0/authorize",
        headers=headers,
        params=params,
        follow_redirects=False,
    )
    return session_token_code_verifier, response.headers["location"]


def get_session_token(client, url: str, session_token_code_verifier: str):
    parsed_url = urllib.parse.urlsplit(url)
    parsed_url_query = urllib.parse.parse_qs(parsed_url.fragment)
    session_token_code = parsed_url_query["session_token_code"][0]

    headers = {
        "User-Agent": "OnlineLounge/" + NSOAPP_VERSION + " NASDKAPI Android",
    }
    body = {
        "client_id": "71b963c1b7b6d119",
        "session_token_code": session_token_code,
        "session_token_code_verifier": session_token_code_verifier,
    }

    response = client.post(
        url="https://accounts.nintendo.com/connect/1.0.0/api/session_token",
        headers=headers,
        data=body,
    )
    return response.json()["session_token"]


class NintendoToken(TypedDict):
    access_token: str
    id_token: str


def get_nintendo_token(client: httpx.Client, session_token: str) -> NintendoToken:
    headers = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2)"}
    body = {
        "client_id": "71b963c1b7b6d119",
        "session_token": session_token,
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token",
    }
    response = client.post(
        url="https://accounts.nintendo.com/connect/1.0.0/api/token",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


class UserInfo(TypedDict):
    nickname: str
    language: str
    country: str
    birthday: str


def get_user_info(client, access_token: str) -> UserInfo:
    headers = {
        "User-Agent": "NASDKAPI; Android",
        "authorization": "Bearer " + access_token,
    }
    user_response = client.get(
        url="https://api.accounts.nintendo.com/2.0.0/users/me",
        headers=headers,
    )
    return user_response.json()


def get_f_token(client: httpx.Client, id_token: str, step: Literal[1, 2]):
    headers = {
        "User-Agent": APP_USER_AGENT,
    }
    body = {"token": id_token, "hashMethod": step}
    response = client.post(
        url="https://api.imink.app/f",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    data = response.json()
    f = data["f"]
    uuid = data["request_id"]
    timestamp = data["timestamp"]
    return f, uuid, timestamp


def get_nso_access_token(client: httpx.Client, id_token: str, user: UserInfo) -> str:
    f, uuid, timestamp = get_f_token(client, id_token, 1)
    body = {
        "parameter": {
            "f": f,
            "language": user["language"],
            "naBirthday": user["birthday"],
            "naCountry": user["country"],
            "naIdToken": id_token,
            "requestId": uuid,
            "timestamp": timestamp,
        }
    }

    headers = {
        "X-Platform": "Android",
        "X-ProductVersion": NSOAPP_VERSION,
        "User-Agent": "com.nintendo.znca/" + NSOAPP_VERSION + "(Android/7.1.2)",
    }

    response = client.post(
        url="https://api-lp1.znc.srv.nintendo.net/v3/Account/Login",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    data = response.json()
    return data["result"]["webApiServerCredential"]["accessToken"]


def get_web_service_token(client: httpx.Client, nso_access_token: str) -> str:
    f, uuid, timestamp = get_f_token(client, nso_access_token, 2)
    headers = {
        "X-Platform": "Android",
        "X-ProductVersion": NSOAPP_VERSION,
        "Authorization": f"Bearer {nso_access_token}",
        "User-Agent": "com.nintendo.znca/" + NSOAPP_VERSION + "(Android/7.1.2)",
    }
    body = {
        "parameter": {
            "f": f,
            "id": 4834290508791808,
            "registrationToken": nso_access_token,
            "requestId": uuid,
            "timestamp": timestamp,
        }
    }
    response = client.post(
        url="https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    data = response.json()
    return data["result"]["accessToken"]


def get_bullet_token(client: httpx.Client, web_service_token: str, user: UserInfo):
    headers = {
        "Content-Type": "application/json",
        "Accept-Language": user["language"],
        "User-Agent": BROWSER_USER_AGENT,
        "X-Web-View-Ver": SPLATNET3_VERSION,
        "X-NACOUNTRY": user["country"],
        "Origin": "https://api.lp1.av5ja.srv.nintendo.net",
        "X-Requested-With": "com.nintendo.znca",
    }
    cookies = {"_gtoken": web_service_token}
    response = client.post(
        url="https://api.lp1.av5ja.srv.nintendo.net/api/bullet_tokens",
        headers=headers,
        cookies=cookies,
    )
    response.raise_for_status()
    data = response.json()
    return data["bulletToken"]


def get_schedule(client: httpx.Client, bullet_token: str):
    headers = {
        "authorization": f"Bearer {bullet_token}",
        "user_agent": BROWSER_USER_AGENT,
        "X-Web-View-Ver": SPLATNET3_VERSION,
    }
    body = {
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "10e1d424391e78d21670227550b3509f",
            }
        },
    }
    response = client.post(
        url="https://api.lp1.av5ja.srv.nintendo.net/api/graphql",
        headers=headers,
        json=body,
    )
    response.raise_for_status()
    return response.json()


def get_bullet_token_from_session_token(
    client: httpx.Client, session_token: str
) -> str:
    nintendo_token = get_nintendo_token(client, session_token)
    user = get_user_info(client, nintendo_token["access_token"])
    nso_access_token = get_nso_access_token(
        client, nintendo_token["access_token"], user
    )
    web_service_token = get_web_service_token(client, nso_access_token)
    bullet_token = get_bullet_token(client, web_service_token, user)
    return bullet_token


if __name__ == "__main__":
    # example full flow
    with httpx.Client() as client:
        verifier, sign_in_url = request_session_token(client)
        print(sign_in_url)
        session_token_url = input("Session token URL: ")
        session_token = get_session_token(client, session_token_url, verifier)
        print(session_token)
        nintendo_token = get_nintendo_token(client, session_token)
        print(nintendo_token)
        user = get_user_info(client, nintendo_token["access_token"])
        print(user)
        nso_access_token = get_nso_access_token(
            client, nintendo_token["access_token"], user
        )
        print(nso_access_token)
        web_service_token = get_web_service_token(client, nso_access_token)
        print(web_service_token)
        bullet_token = get_bullet_token(client, web_service_token, user)
        print(bullet_token)
        schedule = get_schedule(client, bullet_token)
        print(schedule)
