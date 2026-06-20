import mimetypes
import os
import sys
import time
from pathlib import Path

import requests
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_mpserverless20190615.client import Client
from alibabacloud_mpserverless20190615 import models as mp_models


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ID = int(os.environ.get("EMAS_WORKSPACE_ID", "3921191"))
EXISTING_SPACE_ID = os.environ.get("EMAS_SPACE_ID")
SPACE_NAME = os.environ.get("EMAS_SPACE_NAME", "chengkesite")
SPACE_DESC = os.environ.get("EMAS_SPACE_DESC", "chengke growth website")


def client() -> Client:
    config = open_api_models.Config(
        access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
        region_id="cn-hangzhou",
        endpoint="mpserverless.aliyuncs.com",
    )
    return Client(config)


def body_map(response):
    body = getattr(response, "body", response)
    return body.to_map() if hasattr(body, "to_map") else {}


def list_spaces(cli: Client):
    req = mp_models.DescribeSpacesRequest(
        emas_workspace_id=WORKSPACE_ID,
        page_num=1,
        page_size=50,
    )
    data = body_map(cli.describe_spaces(req))
    return data.get("Spaces") or []


def ensure_space(cli: Client) -> str:
    if EXISTING_SPACE_ID:
        print(f"EMAS_SPACE_ID={EXISTING_SPACE_ID}")
        return EXISTING_SPACE_ID

    for space in list_spaces(cli):
        if space.get("Name") == SPACE_NAME:
            space_id = space["SpaceId"]
            print(f"EMAS_SPACE_ID={space_id}")
            return space_id

    req = mp_models.CreateSpaceWithOrderRequest(
        name=SPACE_NAME,
        desc=SPACE_DESC,
        subscription_type="Subscription",
        period=1,
        package_version="free",
        use_coupon=True,
    )
    data = body_map(cli.create_space_with_order(req))
    space_id = data.get("SpaceId")
    if not space_id:
        raise RuntimeError(f"CreateSpaceWithOrder returned no SpaceId: {data}")
    print(f"EMAS_SPACE_ID={space_id}")
    return space_id


def ensure_web_hosting(cli: Client, space_id: str):
    deadline = time.time() + 900
    last_status = None
    while time.time() < deadline:
        try:
            cli.open_web_hosting_service(mp_models.OpenWebHostingServiceRequest(space_id=space_id))
        except Exception as exc:
            message = str(exc)
            if "InvalidSpace.NotInService" in message or "UNINITIALIZED" in message:
                print("WEB_HOSTING_OPEN_WAIT=space_not_ready")
                time.sleep(15)
                continue
            if "already" not in message.lower() and "opened" not in message.lower():
                raise

        data = body_map(cli.get_web_hosting_status(mp_models.GetWebHostingStatusRequest(space_id=space_id)))
        status_data = data.get("Data") or {}
        last_status = status_data.get("Status") or status_data.get("status") or data
        print(f"WEB_HOSTING_STATUS={last_status}")
        if str(last_status).lower() in {"success", "enabled", "online", "open", "opened", "active"}:
            return
        time.sleep(15)
    raise TimeoutError(f"Static hosting did not become ready, last status: {last_status}")


def site_files():
    includes = [
        "index.html",
        "本地生活AI获客系统官网.html",
        "city-growth-engine-data.js",
        "city-growth-engine-data.json",
        "assets",
    ]
    files = []
    for item in includes:
        path = ROOT / item
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix.lower() not in {".mp4", ".mov"}:
                    files.append(child)
    return sorted(files)


def upload_file(cli: Client, space_id: str, file_path: Path):
    rel = file_path.relative_to(ROOT).as_posix()
    hosting_path = "/" + rel
    cred_req = mp_models.GetWebHostingUploadCredentialRequest(
        space_id=space_id,
        file_path=hosting_path,
    )
    data = body_map(cli.get_web_hosting_upload_credential(cred_req)).get("Data") or {}
    endpoint = data.get("Endpoint") or data.get("endpoint")
    if not endpoint:
        raise RuntimeError(f"No upload endpoint for {rel}: {data}")
    if not endpoint.startswith("http"):
        endpoint = "https://" + endpoint

    key = data.get("FilePath") or data.get("filePath") or hosting_path
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    form = {
        "key": key.lstrip("/"),
        "OSSAccessKeyId": data.get("AccessKeyId") or data.get("accessKeyId"),
        "policy": data.get("Policy") or data.get("policy"),
        "Signature": data.get("Signature") or data.get("signature"),
        "x-oss-security-token": data.get("SecurityToken") or data.get("securityToken"),
        "success_action_status": "200",
    }
    form = {k: v for k, v in form.items() if v is not None}
    with file_path.open("rb") as fh:
        resp = requests.post(
            endpoint,
            data=form,
            files={"file": (file_path.name, fh, mime_type)},
            timeout=120,
        )
    if resp.status_code not in {200, 201, 204}:
        raise RuntimeError(f"Upload failed {rel}: {resp.status_code} {resp.text[:500]}")
    print(f"UPLOADED={rel}")


def upload_site(cli: Client, space_id: str):
    files = site_files()
    print(f"UPLOAD_COUNT={len(files)}")
    for file_path in files:
        upload_file(cli, space_id, file_path)


def configure_site(cli: Client, space_id: str):
    req = mp_models.ModifyWebHostingConfigRequest(
        space_id=space_id,
        index_path="index.html",
        error_path="index.html",
        error_http_status="200",
    )
    cli.modify_web_hosting_config(req)
    data = body_map(cli.get_web_hosting_config(mp_models.GetWebHostingConfigRequest(space_id=space_id))).get("Data") or {}
    domain = data.get("DefaultDomain") or data.get("defaultDomain")
    if not domain:
        raise RuntimeError(f"No default domain in web hosting config: {data}")
    url = domain if domain.startswith("http") else "https://" + domain
    print(f"EMAS_DEFAULT_URL={url}")
    return url


def main():
    cli = client()
    space_id = ensure_space(cli)
    ensure_web_hosting(cli, space_id)
    upload_site(cli, space_id)
    configure_site(cli, space_id)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise
